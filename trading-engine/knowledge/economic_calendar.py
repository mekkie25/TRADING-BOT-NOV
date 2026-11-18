"""Report upcoming events and freshness from the local calendar snapshots."""

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import List, Literal, Optional

import pytz


CalendarStatus = Literal["unavailable", "fresh", "stale", "unknown"]
EventTimeKind = Literal["timed", "all_day", "tentative"]


@dataclass(frozen=True)
class EconomicCalendarEvent:
    event_id: str
    event_name: str
    currency: str
    impact: str
    local_date: date
    local_time: Optional[str]
    source_timezone: str
    event_time_utc: Optional[datetime]
    time_kind: EventTimeKind
    scraped_at_utc: Optional[datetime]


@dataclass(frozen=True)
class EconomicCalendarReport:
    status: CalendarStatus
    checked_at_utc: datetime
    last_updated_utc: Optional[datetime]
    events: List[EconomicCalendarEvent]
    summary: str


def _parse_utc_timestamp(value: str, field_name: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field_name} must be an ISO timestamp.") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must include a UTC timezone.")
    return timestamp.astimezone(timezone.utc)


def _parse_event(
    record: dict,
) -> tuple[EconomicCalendarEvent, Optional[datetime]]:
    try:
        event_date = datetime.strptime(record["date"], "%d/%m/%Y").date()
        source_timezone = record["timezone"].strip()
        event_name = record["event"].strip()
        currency = record["currency"].strip().upper()
        impact = record["impact"].strip().lower()
        raw_time = record["time"].strip()
    except (KeyError, AttributeError, TypeError, ValueError) as error:
        raise ValueError("Calendar event is missing valid required fields.") from error

    if not source_timezone or not event_name or not currency:
        raise ValueError("Calendar event timezone, name, and currency are required.")
    try:
        event_zone = pytz.timezone(source_timezone)
    except pytz.UnknownTimeZoneError as error:
        raise ValueError(f"Unknown calendar event timezone: {source_timezone}.") from error

    local_event_time: Optional[datetime] = None
    if raw_time.lower() == "all day":
        time_kind: EventTimeKind = "all_day"
        local_time = None
    elif raw_time.lower() == "tentative":
        time_kind = "tentative"
        local_time = None
    else:
        try:
            parsed_time = datetime.strptime(raw_time, "%H:%M").time()
            local_event_time = event_zone.localize(
                datetime.combine(event_date, parsed_time),
                is_dst=None,
            )
        except (ValueError, pytz.AmbiguousTimeError, pytz.NonExistentTimeError) as error:
            raise ValueError(
                f"Calendar event has an invalid local time: {raw_time}."
            ) from error
        time_kind = "timed"
        local_time = raw_time

    event_time_utc = (
        local_event_time.astimezone(timezone.utc)
        if local_event_time is not None
        else None
    )
    scraped_at_value = str(record.get("scraped_at", "")).strip()
    scraped_at = (
        _parse_utc_timestamp(scraped_at_value, "scraped_at")
        if scraped_at_value
        else None
    )
    event_id = "|".join(
        (
            event_date.isoformat(),
            raw_time,
            currency,
            event_name,
            impact,
        )
    )
    return (
        EconomicCalendarEvent(
            event_id=event_id,
            event_name=event_name,
            currency=currency,
            impact=impact,
            local_date=event_date,
            local_time=local_time,
            source_timezone=source_timezone,
            event_time_utc=event_time_utc,
            time_kind=time_kind,
            scraped_at_utc=scraped_at,
        ),
        scraped_at,
    )


def analyze_economic_calendar(
    output_dir: Path,
    checked_at_utc: datetime,
    stale_after: timedelta,
) -> EconomicCalendarReport:
    """Load all available calendar months and report data freshness explicitly."""
    if checked_at_utc.tzinfo is None or checked_at_utc.utcoffset() != timedelta(0):
        raise ValueError("checked_at_utc must be timezone-aware UTC.")
    if stale_after <= timedelta(0):
        raise ValueError("stale_after must be greater than zero.")

    output_dir = Path(output_dir)
    calendar_files = sorted(
        [
            * (output_dir / "monthly").glob("*.json"),
            * (output_dir / "last_run").glob("*.json"),
        ]
    )
    if not calendar_files:
        return EconomicCalendarReport(
            status="unavailable",
            checked_at_utc=checked_at_utc,
            last_updated_utc=None,
            events=[],
            summary="Calendar data is unavailable: no scraped event files were found.",
        )

    parsed_events = {}
    file_updates: List[datetime] = []
    for path in calendar_files:
        file_updates.append(
            datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        )
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not read calendar data file {path.name}.") from error
        if not isinstance(payload, list):
            raise ValueError(f"Calendar data file {path.name} must contain a list.")

        for record in payload:
            if not isinstance(record, dict):
                raise ValueError(f"Calendar data file {path.name} has an invalid event.")
            event, scraped_at = _parse_event(record)
            existing = parsed_events.get(event.event_id)
            if (
                existing is None
                or scraped_at is None
                or existing.scraped_at_utc is None
                or scraped_at >= existing.scraped_at_utc
            ):
                parsed_events[event.event_id] = event
            if scraped_at is not None:
                file_updates.append(scraped_at)

    last_updated = max(file_updates)
    upcoming = []
    for event in parsed_events.values():
        if event.event_time_utc is not None:
            if event.event_time_utc >= checked_at_utc:
                upcoming.append(event)
            continue

        event_zone = pytz.timezone(event.source_timezone)
        next_day = event.local_date + timedelta(days=1)
        end_of_local_day = event_zone.localize(
            datetime.combine(next_day, time.min),
            is_dst=None,
        ).astimezone(timezone.utc)
        if end_of_local_day >= checked_at_utc:
            upcoming.append(event)

    upcoming.sort(
        key=lambda event: (
            event.event_time_utc or datetime.combine(
                event.local_date,
                time.min,
                tzinfo=timezone.utc,
            ),
            event.currency,
            event.event_name,
        )
    )

    age = checked_at_utc - last_updated
    if age < timedelta(0):
        status: CalendarStatus = "unknown"
        summary = "Calendar freshness is unknown: the latest update time is in the future."
    elif age > stale_after:
        status = "stale"
        summary = (
            f"Calendar data is stale: its latest update was "
            f"{last_updated.isoformat()} UTC, {age} ago."
        )
    else:
        status = "fresh"
        summary = (
            f"Calendar data was updated at {last_updated.isoformat()} UTC; "
            f"{len(upcoming)} upcoming events are available."
        )

    return EconomicCalendarReport(
        status=status,
        checked_at_utc=checked_at_utc,
        last_updated_utc=last_updated,
        events=upcoming,
        summary=summary,
    )
