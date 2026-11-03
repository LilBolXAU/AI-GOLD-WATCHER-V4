"""
High-Impact Economic News Calendar & Blackout Filter for AI GOLD WATCHER V4.
Integrates free institutional ForexFactory economic calendar feed to protect
against high-volatility news events (CPI, NFP, FOMC, Fed Rate Decisions).
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Set
from pathlib import Path
import json
import logging
import requests

logger = logging.getLogger("v4_trading.news_guard")


@dataclass(frozen=True)
class EconomicNewsEvent:
    """Representation of an economic news release."""
    title: str
    country: str
    impact: str  # "High", "Medium", "Low", "Holiday"
    event_time_utc: datetime
    forecast: str = ""
    previous: str = ""


class NewsGuard:
    """
    Automated pre-trade and intra-trade news guardrail.
    Enforces a blackout buffer around high-impact USD economic events.
    Sends alerts before major releases.
    """

    FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

    def __init__(
        self,
        pre_buffer_minutes: int = 15,
        post_buffer_minutes: int = 15,
        alert_advance_minutes: int = 30,
        cache_path: Optional[Path] = None,
        cache_ttl_hours: float = 6.0,
    ):
        self.pre_buffer_minutes = pre_buffer_minutes
        self.post_buffer_minutes = post_buffer_minutes
        self.alert_advance_minutes = alert_advance_minutes
        self.cache_path = cache_path or Path("data/news_calendar_cache.json")
        self.cache_ttl_hours = cache_ttl_hours

        self._events: List[EconomicNewsEvent] = []
        self._last_fetch_time: Optional[datetime] = None
        self._alerted_event_keys: Set[str] = set()

        # Load on startup
        self.refresh_calendar()

    def refresh_calendar(self, force: bool = False) -> bool:
        """Fetch latest weekly calendar from ForexFactory or load from cache."""
        now = datetime.now(timezone.utc)
        if not force and self._last_fetch_time:
            elapsed_hours = (now - self._last_fetch_time).total_seconds() / 3600.0
            if elapsed_hours < self.cache_ttl_hours and self._events:
                return True

        # Try live download
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Gold-Watcher/4.0"}
            resp = requests.get(self.FEED_URL, timeout=6.0, headers=headers)
            if resp.status_code == 200:
                raw_data = resp.json()
                self._parse_and_cache(raw_data, now)
                self._last_fetch_time = now
                logger.info("NewsGuard: Successfully refreshed %d high-impact events.", len(self._events))
                return True
        except Exception as e:
            logger.warning("NewsGuard: Live feed download failed (%s). Attempting local cache fallback...", e)

        # Fallback to local cache file
        return self._load_from_cache()

    def _parse_and_cache(self, raw_data: list, fetch_time: datetime) -> None:
        events: List[EconomicNewsEvent] = []
        for item in raw_data:
            # We filter for USD events with High impact (affects Gold XAUUSD directly)
            country = item.get("country", "")
            impact = item.get("impact", "")
            if country == "USD" and impact == "High":
                raw_date = item.get("date", "")
                try:
                    dt = datetime.fromisoformat(raw_date).astimezone(timezone.utc)
                    events.append(
                        EconomicNewsEvent(
                            title=item.get("title", "High-Impact Release"),
                            country=country,
                            impact=impact,
                            event_time_utc=dt,
                            forecast=item.get("forecast", ""),
                            previous=item.get("previous", ""),
                        )
                    )
                except Exception:
                    continue

        # Sort chronologically
        events.sort(key=lambda x: x.event_time_utc)
        self._events = events

        # Write cache
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_payload = {
                "fetch_time": fetch_time.isoformat(),
                "events": [
                    {
                        "title": e.title,
                        "country": e.country,
                        "impact": e.impact,
                        "event_time_utc": e.event_time_utc.isoformat(),
                        "forecast": e.forecast,
                        "previous": e.previous,
                    }
                    for e in events
                ],
            }
            self.cache_path.write_text(json.dumps(cache_payload, indent=2), encoding="utf-8")
        except Exception as e:
            logger.debug("Failed writing news cache: %s", e)

    def _load_from_cache(self) -> bool:
        if not self.cache_path.exists():
            return False
        try:
            content = json.loads(self.cache_path.read_text(encoding="utf-8"))
            self._events = [
                EconomicNewsEvent(
                    title=item["title"],
                    country=item["country"],
                    impact=item["impact"],
                    event_time_utc=datetime.fromisoformat(item["event_time_utc"]),
                    forecast=item.get("forecast", ""),
                    previous=item.get("previous", ""),
                )
                for item in content.get("events", [])
            ]
            self._last_fetch_time = datetime.fromisoformat(content["fetch_time"])
            logger.info("NewsGuard: Loaded %d events from local cache.", len(self._events))
            return True
        except Exception as e:
            logger.warning("NewsGuard: Failed reading local cache: %s", e)
            return False

    def is_news_blackout(self, current_time: datetime) -> Tuple[bool, Optional[EconomicNewsEvent], str]:
        """
        Check if current_time falls within pre-buffer or post-buffer of any high-impact event.
        Returns: (is_blackout, event, reason)
        """
        # Periodic refresh if stale
        self.refresh_calendar()

        for event in self._events:
            start_blackout = event.event_time_utc - timedelta(minutes=self.pre_buffer_minutes)
            end_blackout = event.event_time_utc + timedelta(minutes=self.post_buffer_minutes)

            if start_blackout <= current_time <= end_blackout:
                mins_to_event = int((event.event_time_utc - current_time).total_seconds() / 60.0)
                if mins_to_event >= 0:
                    timing_str = f"starts in {mins_to_event}m"
                else:
                    timing_str = f"occurred {abs(mins_to_event)}m ago"

                reason = (
                    f"High-impact news blackout active: '{event.title}' ({timing_str}). "
                    f"Trading paused from -{self.pre_buffer_minutes}m to +{self.post_buffer_minutes}m."
                )
                return True, event, reason

        return False, None, "No news blackout."

    def check_upcoming_alert(self, current_time: datetime) -> Optional[Tuple[EconomicNewsEvent, int]]:
        """
        Check if a major event is approaching within alert_advance_minutes and hasn't been alerted yet.
        Returns: (event, minutes_until) or None.
        """
        self.refresh_calendar()

        for event in self._events:
            diff_seconds = (event.event_time_utc - current_time).total_seconds()
            diff_minutes = int(diff_seconds / 60.0)

            # If approaching within advance alert window (e.g. 30 minutes) and event is in the future
            if 0 < diff_minutes <= self.alert_advance_minutes:
                event_key = f"{event.title}_{event.event_time_utc.isoformat()}"
                if event_key not in self._alerted_event_keys:
                    self._alerted_event_keys.add(event_key)
                    return event, diff_minutes

        return None

    def get_next_event(self, current_time: datetime) -> Optional[Tuple[EconomicNewsEvent, int]]:
        """Get the next upcoming High-Impact USD event and minutes until release."""
        for event in self._events:
            diff_seconds = (event.event_time_utc - current_time).total_seconds()
            if diff_seconds > 0:
                diff_minutes = int(diff_seconds / 60.0)
                return event, diff_minutes
        return None
