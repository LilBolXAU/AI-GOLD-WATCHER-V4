"""
Market data validator for AI GOLD WATCHER V4.
Detects missing candles, duplicate timestamps, corrupt OHLC, and bad tick anomalies.
"""

from datetime import timedelta
from typing import List, Sequence
import pandas as pd
from src.data.models import BarData, Timeframe, DataError


class DataValidator:
    """Rigorous validator for financial time-series integrity."""

    @staticmethod
    def validate_bar(bar: BarData) -> None:
        """Validate single candle OHLC invariants."""
        if bar.high < bar.low:
            raise DataError(f"High ({bar.high}) < Low ({bar.low}) at {bar.timestamp}")
        if bar.open < bar.low or bar.open > bar.high:
            raise DataError(f"Open ({bar.open}) outside High-Low at {bar.timestamp}")
        if bar.close < bar.low or bar.close > bar.high:
            raise DataError(f"Close ({bar.close}) outside High-Low at {bar.timestamp}")
        if bar.open <= 0 or bar.high <= 0 or bar.low <= 0 or bar.close <= 0:
            raise DataError(f"Non-positive price detected at {bar.timestamp}")
        if bar.tick_volume < 0:
            raise DataError(f"Negative volume at {bar.timestamp}")

    @classmethod
    def validate_bar_sequence(
        cls, bars: Sequence[BarData], timeframe: Timeframe
    ) -> List[str]:
        """
        Validate sequential continuity, absence of duplicates, and timeframe spacing.
        Returns a list of warning/anomaly strings.
        """
        if not bars:
            return ["Empty bar sequence provided."]

        issues = []
        expected_delta = timedelta(minutes=timeframe.minutes)

        for i in range(len(bars)):
            cls.validate_bar(bars[i])
            if i > 0:
                prev_ts = bars[i - 1].timestamp
                curr_ts = bars[i].timestamp

                if curr_ts <= prev_ts:
                    issues.append(
                        f"Non-monotonic timestamp or duplicate: {prev_ts} -> {curr_ts}"
                    )
                else:
                    diff = curr_ts - prev_ts
                    # Allow for weekend gap (Friday 22:00 to Sunday 22:00 UTC)
                    if diff > expected_delta and curr_ts.weekday() != 6:
                        # Intra-week missing candle gap
                        missing_count = int(diff / expected_delta) - 1
                        if missing_count > 0:
                            issues.append(
                                f"Gap detected: {missing_count} missing {timeframe.value} bars between {prev_ts} and {curr_ts}"
                            )

        return issues

    @staticmethod
    def detect_bad_spikes(bars: List[BarData], threshold_pts: float = 300.0) -> List[int]:
        """
        Detect one-bar spike outliers (bad ticks) that immediately revert.
        Returns list of bar indices that exhibit aberrant spike behavior.
        """
        if len(bars) < 3:
            return []

        spike_indices = []
        for i in range(1, len(bars) - 1):
            prev_close = bars[i - 1].close
            curr_bar = bars[i]
            next_open = bars[i + 1].open

            up_spike = (curr_bar.high - prev_close > threshold_pts * 0.01) and (
                curr_bar.high - next_open > threshold_pts * 0.01
            )
            down_spike = (prev_close - curr_bar.low > threshold_pts * 0.01) and (
                next_open - curr_bar.low > threshold_pts * 0.01
            )

            if up_spike or down_spike:
                spike_indices.append(i)

        return spike_indices
