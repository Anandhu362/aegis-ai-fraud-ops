"""Pure mathematical geolocation, haversine distance, and travel speed logic."""

import math
from datetime import datetime

from aegis_common.schemas.enums import Channel
from aegis_common.schemas.features import TravelCheck

EARTH_RADIUS_KM: float = 6371.0
IMPOSSIBLE_TRAVEL_SPEED_KMH: float = 800.0
MIN_DISTANCE_IMPOSSIBLE_TRAVEL_KM: float = 200.0
CARD_PRESENT_EXEMPTION_KM: float = 50.0
MIN_ELAPSED_MINUTES: float = 1.0


def compute_haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate the great-circle distance between two geographic points in kilometers.

    Args:
        lat1: Latitude of point 1 in degrees [-90, 90].
        lon1: Longitude of point 1 in degrees [-180, 180].
        lat2: Latitude of point 2 in degrees [-90, 90].
        lon2: Longitude of point 2 in degrees [-180, 180].

    Returns:
        Great-circle distance in kilometers.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (
        math.sin(delta_lambda / 2.0) ** 2
    )
    # Clamp to prevent float inaccuracies from exceeding domain of asin [-1, 1]
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.asin(math.sqrt(a))
    return round(EARTH_RADIUS_KM * c, 2)


def compute_travel_speed(distance_km: float, elapsed_seconds: float) -> float:
    """Compute travel speed in km/h with minimum elapsed time clamp.

    Args:
        distance_km: Distance traversed in kilometers.
        elapsed_seconds: Elapsed time between transactions in seconds.

    Returns:
        Effective travel speed in km/h.
    """
    elapsed_minutes = max(MIN_ELAPSED_MINUTES, elapsed_seconds / 60.0)
    elapsed_hours = elapsed_minutes / 60.0
    return round(distance_km / elapsed_hours, 2)


def evaluate_travel(
    lat1: float,
    lon1: float,
    ts1: datetime,
    channel1: Channel,
    lat2: float,
    lon2: float,
    ts2: datetime,
    channel2: Channel,
    prev_city: str | None = None,
) -> TravelCheck:
    """Evaluate travel feasibility between two consecutive transactions.

    Args:
        lat1: Origin latitude.
        lon1: Origin longitude.
        ts1: Origin timestamp.
        channel1: Origin payment channel.
        lat2: Destination latitude.
        lon2: Destination longitude.
        ts2: Destination timestamp.
        channel2: Destination payment channel.
        prev_city: Name of previous city.

    Returns:
        TravelCheck signal model with speed, distance, and impossible travel flag.
    """
    distance_km = compute_haversine_distance(lat1, lon1, lat2, lon2)
    elapsed_seconds = abs((ts2 - ts1).total_seconds())
    elapsed_minutes = round(max(MIN_ELAPSED_MINUTES, elapsed_seconds / 60.0), 2)
    speed_kmh = compute_travel_speed(distance_km, elapsed_seconds)

    # Exemption rule: card present transactions in same urban zone (<50km)
    is_exempt = (
        channel1 == Channel.CARD_PRESENT
        and channel2 == Channel.CARD_PRESENT
        and distance_km <= CARD_PRESENT_EXEMPTION_KM
    )

    is_impossible = (
        not is_exempt
        and distance_km >= MIN_DISTANCE_IMPOSSIBLE_TRAVEL_KM
        and speed_kmh > IMPOSSIBLE_TRAVEL_SPEED_KMH
    )

    return TravelCheck(
        prev_city=prev_city,
        distance_km=distance_km,
        elapsed_min=elapsed_minutes,
        speed_kmh=speed_kmh,
        impossible=is_impossible,
        exempt=is_exempt,
    )
