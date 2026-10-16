"""Google Cloud Firestore and BigQuery TelemetrySink adapter.

Streams live agent investigation milestones and persists final verdicts to:
- Cloud Firestore: `investigations/{tx_id}` and `investigations/{tx_id}/events/{seq:04d}`
- BigQuery: `fraud_telemetry.investigation_results`
"""

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

from aegis_common.logging import get_logger
from aegis_common.schemas.telemetry import TelemetryEvent
from aegis_common.schemas.verdict import Verdict
from google.cloud import bigquery, firestore

logger = get_logger("aegis.gcp.telemetry")


_GCP_FIRESTORE_CLIENTS: dict[str, firestore.Client] = {}
_GCP_BIGQUERY_CLIENTS: dict[str, bigquery.Client] = {}


class FirestoreTelemetrySinkAdapter:
    """Production TelemetrySink adapter persisting events to Firestore & BigQuery."""

    def __init__(
        self,
        project_id: str = "aegis-fraud-ops-2026",
        bq_dataset: str = "fraud_telemetry",
    ) -> None:
        self.project_id = project_id
        self.bq_dataset = bq_dataset

    def _get_firestore(self) -> firestore.Client:
        if self.project_id not in _GCP_FIRESTORE_CLIENTS:
            _GCP_FIRESTORE_CLIENTS[self.project_id] = firestore.Client(project=self.project_id)
        return _GCP_FIRESTORE_CLIENTS[self.project_id]

    def _get_bigquery(self) -> bigquery.Client:
        if self.project_id not in _GCP_BIGQUERY_CLIENTS:
            _GCP_BIGQUERY_CLIENTS[self.project_id] = bigquery.Client(project=self.project_id)
        return _GCP_BIGQUERY_CLIENTS[self.project_id]

    async def emit_event(self, tx_id: str, event: TelemetryEvent) -> None:
        """Stream an ordered telemetry milestone to Firestore non-blockingly."""
        logger.info(
            "Emitting telemetry event",
            tx_id=tx_id,
            seq=event.seq,
            agent=event.agent,
            action=event.action,
        )

        loop = asyncio.get_running_loop()
        # Run in thread pool without blocking agent decision loop
        loop.run_in_executor(None, self._sync_emit_event, tx_id, event)

    def _sync_emit_event(self, tx_id: str, event: TelemetryEvent) -> None:
        try:
            db = self._get_firestore()
            doc_ref = (
                db.collection("investigations")
                .document(tx_id)
                .collection("events")
                .document(f"{event.seq:04d}")
            )

            action_val = (
                event.action.value if hasattr(event.action, "value") else str(event.action)
            )
            data: dict[str, Any] = {
                "seq": event.seq,
                "agent": event.agent,
                "action": action_val,
                "severity": event.severity,
                "message": event.message,
                "data": event.data or {},
                "latency_ms": event.latency_ms,
                "timestamp": event.timestamp.isoformat()
                if hasattr(event.timestamp, "isoformat")
                else str(event.timestamp),
            }

            doc_ref.set(data)
        except Exception as exc:
            logger.warn(
                "Failed to write event to Firestore",
                tx_id=tx_id,
                seq=event.seq,
                error=str(exc),
            )

    async def save_verdict(self, verdict: Verdict) -> None:
        """Persist final verdict document to Firestore and BigQuery non-blockingly."""
        logger.info(
            "Persisting verdict to Firestore & BigQuery",
            tx_id=verdict.tx_id,
            decision=verdict.decision,
            score=verdict.threat_score,
        )

        loop = asyncio.get_running_loop()
        # Persist concurrently in thread pool to preserve pipeline SLO
        loop.run_in_executor(None, self._sync_save_verdict, verdict)

    def _sync_save_verdict(self, verdict: Verdict) -> None:
        # 1. Write to Firestore
        try:
            db = self._get_firestore()
            doc_ref = db.collection("investigations").document(verdict.tx_id)

            verdict_dict = verdict.model_dump(mode="json")
            verdict_dict["updated_at"] = datetime.now(UTC).isoformat()

            doc_ref.set(verdict_dict, merge=True)
            logger.info("Verdict persisted in Firestore", tx_id=verdict.tx_id)
        except Exception as exc:
            logger.error(
                "Failed to persist verdict to Firestore",
                tx_id=verdict.tx_id,
                error=str(exc),
            )

        # 2. Stream to BigQuery
        try:
            bq = self._get_bigquery()
            table_id = f"{self.project_id}.{self.bq_dataset}.investigation_results"

            score_bd = verdict.score_breakdown
            rules = score_bd.rules if score_bd else []
            signals_json = (
                json.dumps(score_bd.signals) if score_bd and score_bd.signals else "{}"
            )
            llm_adj = score_bd.llm_adjustment if score_bd else 0

            row = [
                {
                    "tx_id": verdict.tx_id,
                    "user_id": verdict.user_id,
                    "completed_at": datetime.now(UTC).isoformat(),
                    "amount": float(getattr(verdict, "amount", 0.0) or 0.0),
                    "currency": "USD",
                    "merchant": getattr(verdict, "merchant", "") or "",
                    "merchant_category": getattr(verdict, "merchant_category", "") or "",
                    "threat_score": int(verdict.threat_score),
                    "risk_level": verdict.risk_level.value
                    if hasattr(verdict.risk_level, "value")
                    else str(verdict.risk_level),
                    "decision": verdict.decision.value
                    if hasattr(verdict.decision, "value")
                    else str(verdict.decision),
                    "typology": verdict.typology.value
                    if hasattr(verdict.typology, "value")
                    else str(verdict.typology),
                    "degraded": bool(verdict.degraded),
                    "llm_adjustment": int(llm_adj),
                    "signals": signals_json,
                    "rules": rules,
                    "latency_total_ms": (
                        int(verdict.latency_ms.total) if verdict.latency_ms else 0
                    ),
                    "model_orchestrator": "gemini-2.5-flash",
                    "model_specialist": "gemini-flash-lite-latest",
                }
            ]

            errors = bq.insert_rows_json(table_id, row)
            if errors:
                logger.warn("BigQuery insert errors", errors=errors, tx_id=verdict.tx_id)
            else:
                logger.info("Verdict streamed to BigQuery", tx_id=verdict.tx_id)
        except Exception as exc:
            logger.error(
                "Failed to stream verdict to BigQuery",
                tx_id=verdict.tx_id,
                error=str(exc),
            )
