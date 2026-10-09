"""Static fixture table for IP reputation and Tor detection in mock mode."""

from aegis_common.schemas.features import IpReputation

TOR_EXIT_NODES: frozenset[str] = frozenset(
    {
        "185.220.101.5",
        "185.220.101.6",
        "185.220.101.7",
        "198.98.56.12",
        "51.15.43.205",
    }
)

VPN_HOSTING_IPS: frozenset[str] = frozenset(
    {
        "104.28.0.1",
        "195.181.160.1",
        "45.33.32.156",
    }
)


class StaticIpIntelAdapter:
    """Mock IP intelligence adapter backed by static in-memory sets."""

    async def lookup_ip(self, ip_address: str | None) -> IpReputation:
        """Lookup IP address reputation against known fixtures."""
        if not ip_address:
            return IpReputation(unknown=True)

        is_tor = ip_address in TOR_EXIT_NODES
        is_vpn = ip_address in VPN_HOSTING_IPS

        if is_tor:
            return IpReputation(
                is_tor=True,
                is_vpn=False,
                is_hosting=True,
                asn="AS60729",
                asn_type="HOSTING",
                abuse_score=95,
                country="DE",
                unknown=False,
            )

        if is_vpn:
            return IpReputation(
                is_tor=False,
                is_vpn=True,
                is_hosting=True,
                asn="AS13335",
                asn_type="HOSTING",
                abuse_score=40,
                country="US",
                unknown=False,
            )

        # Clean residential IP default
        return IpReputation(
            is_tor=False,
            is_vpn=False,
            is_hosting=False,
            asn="AS7922",
            asn_type="ISP",
            abuse_score=0,
            country="US",
            unknown=False,
        )
