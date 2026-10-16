"""HTTP dispatcher adapter forwarding transactions to agent-engine service."""

import asyncio
from typing import Any

import httpx
from aegis_common.errors import ModelInferenceError
from aegis_common.logging import get_logger
from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import Verdict

logger = get_logger("aegis.gateway.dispatcher")


class HttpInvestigationDispatcher:
    """Dispatches transactions to agent-engine via HTTP with persistent pooling and retry."""

    def __init__(self, engine_base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.engine_base_url = engine_base_url.rstrip("/")
        self._client = client
        self._shared_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        if self._shared_client is None or self._shared_client.is_closed:
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
            self._shared_client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=15.0),
                limits=limits,
            )
        return self._shared_client

    async def dispatch_sync(self, tx: Transaction) -> Verdict:
        """Call agent-engine /internal/investigate and parse returned Verdict with
        cold-start retry.
        """
        client = await self._get_client()
        url = f"{self.engine_base_url}/internal/investigate"
        payload = tx.model_dump(mode="json")

        max_attempts = 3
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.post(url, json=payload)

                if response.status_code == httpx.codes.OK:
                    data: dict[str, Any] = response.json()
                    return Verdict.model_validate(data)

                # Retry on 502/503 during cold starts or deployment shifts
                if response.status_code in (502, 503) and attempt < max_attempts:
                    logger.warn(
                        "Agent engine transient status, retrying for cold start warm-up",
                        status=response.status_code,
                        attempt=attempt,
                    )
                    await asyncio.sleep(1.2 * attempt)
                    continue

                logger.error(
                    "Engine investigate failed",
                    status=response.status_code,
                    body=response.text[:200],
                )
                raise ModelInferenceError(
                    f"Agent engine returned status {response.status_code}",
                    detail=response.text[:200],
                )
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt < max_attempts:
                    logger.warn(
                        "Engine connection transient error, retrying for cold start warm-up",
                        attempt=attempt,
                        error=str(exc),
                    )
                    await asyncio.sleep(1.5 * attempt)
                    continue
                break

        logger.error("Engine network error after retries", error=str(last_error))
        raise ModelInferenceError(
            "Failed to reach agent-engine service",
            detail=str(last_error),
        ) from last_error

    async def dispatch_async(self, tx: Transaction) -> dict[str, str]:
        """Call agent-engine /internal/pubsub/tx-ingested or publish message."""
        client = await self._get_client()
        url = f"{self.engine_base_url}/internal/pubsub/tx-ingested"

        try:
            payload = tx.model_dump(mode="json")
            response = await client.post(url, json=payload)

            if response.status_code not in (200, 202):
                raise ModelInferenceError(
                    f"Agent engine push failed with status {response.status_code}",
                    detail=response.text[:200],
                )

            return {
                "tx_id": tx.tx_id,
                "status": "QUEUED",
                "status_url": f"/v1/investigations/{tx.tx_id}",
            }
        except httpx.RequestError as exc:
            logger.error("Async dispatch network error", error=str(exc))
            raise ModelInferenceError(
                "Failed to publish transaction to ingestion queue",
                detail=str(exc),
            ) from exc
