"""ADK Enrichment Tool: Query IP threat intelligence and Tor exit node lists."""

from aegis_common.schemas.features import IpReputation

from aegis_engine.ports.ip_intel import IpIntelPort


async def lookup_ip_reputation(
    ip_address: str | None,
    ip_intel: IpIntelPort,
) -> IpReputation:
    """Lookup IP address reputation against Tor, VPN, and ASN intelligence sources.

    Args:
        ip_address: Client IP address string or None.
        ip_intel: IpIntelPort port implementation.

    Returns:
        IpReputation signal model.
    """
    return await ip_intel.lookup_ip(ip_address)
