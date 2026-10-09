"""Statistical deviation, monetary anomalies, velocity windowing, and structuring detection."""

from collections.abc import Sequence
from datetime import datetime

from aegis_common.schemas.features import MonetaryAnomaly, UserBaseline, VelocityStats

STD_FLOOR: float = 5.0
Z_SCORE_ANOMALY_THRESHOLD: float = 3.0
P95_RATIO_ANOMALY_THRESHOLD: float = 2.5
Z_SCORE_CLAMP_MIN: float = -10.0
Z_SCORE_CLAMP_MAX: float = 10.0

STRUCTURING_MIN_AMOUNT: float = 8000.0
STRUCTURING_MAX_AMOUNT: float = 10000.0
STRUCTURING_PRIOR_HITS_REQUIRED: int = 2
STRUCTURING_WINDOW_SECONDS: float = 900.0  # 15 minutes
BURST_WINDOW_SECONDS: float = 60.0  # 60 seconds
BURST_THRESHOLD_COUNT: int = 5  # >= 5 txs in 60s


def compute_monetary_anomaly(amount: float, baseline: UserBaseline) -> MonetaryAnomaly:
    """Compute statistical amount deviations against historical 90-day baseline.

    Args:
        amount: Transaction amount.
        baseline: User historical baseline.

    Returns:
        MonetaryAnomaly signal model with Z-score and percentile ratios.
    """
    effective_std = max(baseline.std_amount, STD_FLOOR)
    raw_z = (amount - baseline.avg_amount) / effective_std
    z_score = round(max(Z_SCORE_CLAMP_MIN, min(Z_SCORE_CLAMP_MAX, raw_z)), 2)

    p95 = max(baseline.p95_amount, 1.0)
    ratio_to_p95 = round(amount / p95, 2)

    median = max(baseline.median_amount, 1.0)
    ratio_to_median = round(amount / median, 2)

    is_anomalous = (
        z_score >= Z_SCORE_ANOMALY_THRESHOLD or ratio_to_p95 > P95_RATIO_ANOMALY_THRESHOLD
    )

    return MonetaryAnomaly(
        z_score=z_score,
        ratio_to_p95=ratio_to_p95,
        ratio_to_median=ratio_to_median,
        is_anomalous=is_anomalous,
    )


def is_in_structuring_band(amount: float) -> bool:
    """Return True if amount falls within the $8,000-$9,999 near-threshold structuring band."""
    return STRUCTURING_MIN_AMOUNT <= amount < STRUCTURING_MAX_AMOUNT


def compute_velocity_stats(
    current_amount: float,
    current_ts: datetime,
    recent_transactions: Sequence[tuple[datetime, float]],
) -> VelocityStats:
    """Evaluate sliding-window velocity bursts and near-threshold structuring smurfing.

    Args:
        current_amount: Value of current transaction.
        current_ts: Timestamp of current transaction.
        recent_transactions: Prior transactions as list of (timestamp, amount) tuples.

    Returns:
        VelocityStats with 60s burst counts, 15m counts, and structuring indicators.
    """
    in_structuring = is_in_structuring_band(current_amount)

    # 1 counts for the current transaction
    count_60s = 1
    count_15m = 1
    near_threshold_prior_15m = 0

    for tx_ts, tx_amount in recent_transactions:
        delta_sec = (current_ts - tx_ts).total_seconds()
        # Only consider prior transactions that occurred before current_ts
        if 0 < delta_sec <= BURST_WINDOW_SECONDS:
            count_60s += 1
        if 0 < delta_sec <= STRUCTURING_WINDOW_SECONDS:
            count_15m += 1
            if is_in_structuring_band(tx_amount):
                near_threshold_prior_15m += 1

    structuring_hit = in_structuring and (
        near_threshold_prior_15m >= STRUCTURING_PRIOR_HITS_REQUIRED
    )

    return VelocityStats(
        count_60s=count_60s,
        count_15m=count_15m,
        near_threshold_count_15m=near_threshold_prior_15m + (1 if in_structuring else 0),
        in_structuring_band=in_structuring,
        structuring_hit=structuring_hit,
    )
