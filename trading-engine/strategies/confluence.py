"""Count strategy confluence without creating an entry trigger."""

from dataclasses import dataclass
from typing import Dict, Iterable, Literal, Optional, Tuple


ConfluenceGroup = Literal[
    "direction",
    "level_alignment",
    "location",
    "timing_volume",
    "candle_confirmation",
    "other",
]
ConfluenceCountMode = Literal["groups", "reasons"]


@dataclass(frozen=True)
class ConfluenceReason:
    name: str
    group: ConfluenceGroup
    present: bool
    detail: str = ""


@dataclass(frozen=True)
class ConfluenceReport:
    reasons: Tuple[ConfluenceReason, ...]
    present_reasons: Tuple[str, ...]
    present_groups: Tuple[str, ...]
    reason_count: int
    group_count: int
    minimum_count: int
    count_mode: ConfluenceCountMode
    meets_minimum: bool
    starts_trade: bool = False


def count_confluence(
    reasons: Iterable[ConfluenceReason],
    minimum_count: int = 0,
    count_mode: ConfluenceCountMode = "groups",
) -> ConfluenceReport:
    if isinstance(minimum_count, bool) or not isinstance(minimum_count, int) or minimum_count < 0:
        raise ValueError("minimum_count must be a non-negative integer.")
    if count_mode not in ("groups", "reasons"):
        raise ValueError("count_mode must be 'groups' or 'reasons'.")
    all_reasons = tuple(reasons)
    if any(not reason.name.strip() for reason in all_reasons):
        raise ValueError("Confluence reason names must not be empty.")
    present = tuple(reason for reason in all_reasons if reason.present)
    present_names = tuple(reason.name for reason in present)
    groups = tuple(sorted({reason.group for reason in present}))
    reason_count = len(present)
    group_count = len(groups)
    count = group_count if count_mode == "groups" else reason_count
    return ConfluenceReport(
        reasons=all_reasons,
        present_reasons=present_names,
        present_groups=groups,
        reason_count=reason_count,
        group_count=group_count,
        minimum_count=minimum_count,
        count_mode=count_mode,
        meets_minimum=count >= minimum_count,
    )


def confluence_from_mapping(
    values: Dict[str, Optional[bool]],
    groups: Optional[Dict[str, ConfluenceGroup]] = None,
    minimum_count: int = 0,
    count_mode: ConfluenceCountMode = "groups",
) -> ConfluenceReport:
    mapped_groups = groups or {}
    reasons = tuple(
        ConfluenceReason(
            name=name,
            group=mapped_groups.get(name, "other"),
            present=value is True,
            detail="unknown" if value is None else "",
        )
        for name, value in values.items()
    )
    return count_confluence(reasons, minimum_count, count_mode)
