"""ADK Enrichment Tool: Validate client device identity and novelty."""

from aegis_common.schemas.features import DeviceCheck

from aegis_engine.ports.profile_store import ProfileStore


async def check_device(
    user_id: str,
    device_id: str,
    profile_store: ProfileStore,
) -> DeviceCheck:
    """Check if the transaction device identifier is in customer's historical profile.

    Args:
        user_id: Customer identifier.
        device_id: Client device hardware/browser hash.
        profile_store: ProfileStore port implementation.

    Returns:
        DeviceCheck signal model with is_new flag.
    """
    is_known = await profile_store.is_known_device(user_id, device_id)
    return DeviceCheck(is_new=not is_known)
