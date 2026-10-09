"""Hexagonal port protocol for IP reputation and intelligence lookup."""

from typing import Protocol

from aegis_common.schemas.features import IpReputation


class IpIntelPort(Protocol):
    """Port for IP reputation, Tor detection, and ASN intelligence."""

    async def lookup_ip(self, ip_address: str | None) -> IpReputation:
        """Query IP threat intelligence.

        Args:
            ip_address: IPv4 or IPv6 address string (or None if card-present).

        Returns:
            IpReputation model.
        """
        ...
