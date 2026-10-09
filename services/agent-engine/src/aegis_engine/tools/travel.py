"""ADK Enrichment Tool: Verify physical travel velocity against previous transaction."""

from datetime import datetime

from aegis_common.schemas.enums import Channel
from aegis_common.schemas.features import TravelCheck

from aegis_engine.domain.geo import evaluate_travel
from aegis_engine.ports.profile_store import ProfileStore


async def verify_velocity_travel(
    user_id: str,
    current_lat: float,
    current_lon: float,
    current_ts: datetime,
    current_channel: Channel,
    profile_store: ProfileStore,
) -> TravelCheck:
    """Verify physical travel velocity against customer's previous transaction.

    Args:
        user_id: Customer identifier.
        current_lat: Current transaction latitude.
        current_lon: Current transaction longitude.
        current_ts: Current transaction timestamp.
        current_channel: Current payment channel (CARD_PRESENT vs ECOMMERCE).
        profile_store: ProfileStore port implementation.

    Returns:
        TravelCheck signal model with speed, distance, and impossible travel flag.
    """
    last_tx = await profile_store.get_last_transaction_location(user_id)
    if not last_tx:
        # First transaction for this user
        return TravelCheck()

    prev_lat = float(last_tx["lat"])
    prev_lon = float(last_tx["lon"])
    prev_ts = last_tx["ts"]
    prev_channel = last_tx.get("channel", Channel.CARD_PRESENT)
    prev_city = last_tx.get("city")

    return evaluate_travel(
        lat1=prev_lat,
        lon1=prev_lon,
        ts1=prev_ts,
        channel1=prev_channel,
        lat2=current_lat,
        lon2=current_lon,
        ts2=current_ts,
        channel2=current_channel,
        prev_city=prev_city,
    )
