"""ADK Enrichment Tool: Compute sliding-window velocity and structuring smurfing."""

from datetime import datetime

from aegis_common.schemas.features import VelocityStats

from aegis_engine.domain.velocity import compute_velocity_stats
from aegis_engine.ports.profile_store import ProfileStore


async def get_velocity_window(
    user_id: str,
    current_amount: float,
    current_ts: datetime,
    profile_store: ProfileStore,
) -> VelocityStats:
    """Evaluate burst velocity and near-threshold structuring from recent transaction buffer.

    Args:
        user_id: Customer identifier.
        current_amount: Value of current transaction.
        current_ts: Timestamp of current transaction.
        profile_store: ProfileStore port implementation.

    Returns:
        VelocityStats signal model.
    """
    recent_txs = await profile_store.get_recent_transactions(user_id, limit=50)
    return compute_velocity_stats(current_amount, current_ts, recent_txs)
