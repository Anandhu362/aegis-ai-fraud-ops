"""ADK Enrichment Tool: Retrieve historical 90-day baseline for customer."""

from aegis_common.schemas.features import UserBaseline

from aegis_engine.ports.profile_store import ProfileStore


async def get_user_baseline(
    user_id: str,
    profile_store: ProfileStore,
) -> UserBaseline:
    """Retrieve historical 90-day baseline for customer from ProfileStore.

    Args:
        user_id: Customer identifier.
        profile_store: ProfileStore port implementation.

    Returns:
        UserBaseline model.
    """
    return await profile_store.get_baseline(user_id)
