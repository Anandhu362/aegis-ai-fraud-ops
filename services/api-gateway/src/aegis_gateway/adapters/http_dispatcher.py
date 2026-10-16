"""HTTP dispatcher adapter forwarding transactions to agent-engine service."""

from typing import Any

import httpx
from aegis_common.errors import ModelInferenceError
from aegis_common.logging import get_logger
from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import Verdict

logger = get_logger("aegis.gateway.dispatcher")


class HttpInvestigationDispatcher:
    """Dispatches transactions to agent-engine via HTTP."""

    def __init__(self, engine_base_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.engine_base_url = engine_base_url.rstrip("/")
        self._client = client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(timeout=35.0)

    async def dispatch_sync(self, tx: Transaction) -> Verdict:
        """Call agent-engine /internal/investigate and parse returned Verdict."""
        client = await self._get_client()
        url = f"{self.engine_base_url}/internal/investigate"

        try:
            payload = tx.model_dump(mode="json")
            response = await client.post(url, json=payload)

            if response.status_code != httpx.codes.OK:
                logger.error(
                    "Engine investigate failed",
                    status=response.status_code,
                    body=response.text[:200],
                )
                raise ModelInferenceError(
                    f"Agent engine returned status {response.status_code}",
                    detail=response.text[:200],
                )

            data: dict[str, Any] = response.json()
            return Verdict.model_validate(data)
        except httpx.RequestError as exc:
            logger.error("Engine network error", error=str(exc))
            raise ModelInferenceError(
                "Failed to reach agent-engine service",
                detail=str(exc),
            ) from exc

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
