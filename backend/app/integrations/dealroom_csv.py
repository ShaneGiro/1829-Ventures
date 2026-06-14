"""Dealroom CSV parsing and normalization.

Dealroom exports include metadata rows before the real header, then store many
one-to-many values as semicolon-delimited arrays inside individual cells.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from app.core.constants import DEFAULT_SECTOR

HEADER_MARKERS = ("ID", "Name", "Dealroom URL")
MISSING_VALUES = {"", "n/a", "na", "null", "none", "-"}


@dataclass(frozen=True)
class DealroomFounder:
    name: str
    status: str | None = None
    gender: str | None = None
    university: str | None = None
    linkedin_url: str | None = None
    background: str | None = None


@dataclass(frozen=True)
class DealroomFundingRound:
    round_type: str | None
    amount: Decimal | None
    currency: str | None
    date: str | None
    investors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DealroomParsedRow:
    row_number: int
    raw: dict[str, str]
    dealroom_id: str | None
    name: str | None
    dealroom_url: str | None
    website: str | None
    domain: str | None
    tagline: str | None
    description: str | None
    stage: str | None
    sector: str
    sector_warnings: list[str]
    industries: list[str]
    sub_industries: list[str]
    tags: list[str]
    city: str | None
    state: str | None
    country: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    founders: list[DealroomFounder]
    funding_rounds: list[DealroomFundingRound]


@dataclass(frozen=True)
class DealroomParseResult:
    header_row_number: int
    metadata_rows: list[list[str]]
    headers: list[str]
    rows: list[DealroomParsedRow]


def parse_dealroom_csv(content: bytes | str) -> DealroomParseResult:
    """Parse a Dealroom CSV export into normalized rows."""
    text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
    reader = csv.reader(io.StringIO(text))
    raw_rows = list(reader)
    header_index = _find_header_index(raw_rows)
    headers = [header.strip() for header in raw_rows[header_index]]

    parsed_rows: list[DealroomParsedRow] = []
    for index, row in enumerate(raw_rows[header_index + 1 :], start=header_index + 2):
        raw = _row_to_dict(headers, row)
        if not any(value.strip() for value in raw.values()):
            continue
        parsed_rows.append(_parse_row(index, raw))

    return DealroomParseResult(
        header_row_number=header_index + 1,
        metadata_rows=raw_rows[:header_index],
        headers=headers,
        rows=parsed_rows,
    )


def split_semicolon(value: str | None) -> list[str | None]:
    """Split Dealroom's semicolon arrays while preserving empty positions."""
    if value is None:
        return []
    if value == "":
        return []
    return [_clean_value(part) for part in value.split(";")]


def normalize_domain(website: str | None) -> str | None:
    value = _clean_value(website)
    if value is None:
        return None
    parsed = urlparse(value if "://" in value else f"https://{value}")
    host = (parsed.netloc or parsed.path).lower()
    host = host.removeprefix("www.")
    return host.rstrip("/") or None


def map_dealroom_sector(industries: list[str], sub_industries: list[str]) -> tuple[str, list[str]]:
    """Map Dealroom industries to 1829's five-sector taxonomy."""
    haystack = " ".join([*industries, *sub_industries]).lower()
    rules: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "Photonics, Imaging & Quantum",
            ("photon", "imaging", "quantum", "optics", "sensor", "semiconductor"),
        ),
        (
            "Clean Tech & Energy",
            (
                "clean",
                "climate",
                "energy",
                "battery",
                "carbon",
                "solar",
                "recycling",
                "sustainab",
                "green",
            ),
        ),
        (
            "Life Sciences & Health Tech",
            (
                "health",
                "medical",
                "bio",
                "life science",
                "pharma",
                "therapeutic",
                "diagnostic",
                "patient",
            ),
        ),
        (
            "Intelligent Systems, AI & Cyber",
            (
                "artificial intelligence",
                "machine learning",
                "robot",
                "cyber",
                "security",
                "software",
                "enterprise",
                "automation",
                "data",
                "defence",
                "defense",
                "drone",
            ),
        ),
    )
    for sector, needles in rules:
        if any(needle in haystack for needle in needles):
            return sector, []
    if industries or sub_industries:
        return DEFAULT_SECTOR, ["unmapped_dealroom_taxonomy"]
    return DEFAULT_SECTOR, ["missing_dealroom_taxonomy"]


def _find_header_index(rows: list[list[str]]) -> int:
    for index, row in enumerate(rows):
        normalized = {cell.strip() for cell in row}
        if all(marker in normalized for marker in HEADER_MARKERS):
            return index
    raise ValueError("Could not find Dealroom header row")


def _row_to_dict(headers: list[str], row: list[str]) -> dict[str, str]:
    values = [*row, *([""] * max(len(headers) - len(row), 0))]
    return dict(zip(headers, values[: len(headers)], strict=False))


def _parse_row(row_number: int, raw: dict[str, str]) -> DealroomParsedRow:
    industries = _clean_list(split_semicolon(raw.get("Industries")))
    sub_industries = _clean_list(split_semicolon(raw.get("Sub industries")))
    sector, sector_warnings = map_dealroom_sector(industries, sub_industries)
    website = _clean_value(raw.get("Website"))
    return DealroomParsedRow(
        row_number=row_number,
        raw=raw,
        dealroom_id=_clean_value(raw.get("ID")),
        name=_clean_value(raw.get("Name")),
        dealroom_url=_clean_value(raw.get("Dealroom URL")),
        website=website,
        domain=normalize_domain(website),
        tagline=_clean_value(raw.get("Tagline")),
        description=_clean_value(raw.get("Long description")) or _clean_value(raw.get("Tagline")),
        stage=_clean_value(raw.get("Growth stage")) or _clean_value(raw.get("Last round")),
        sector=sector,
        sector_warnings=sector_warnings,
        industries=industries,
        sub_industries=sub_industries,
        tags=_clean_list(split_semicolon(raw.get("All tags") or raw.get("Tags"))),
        city=_clean_value(raw.get("HQ city")),
        state=_clean_value(raw.get("HQ state")),
        country=_clean_value(raw.get("HQ country")),
        latitude=_decimal_or_none(raw.get("Latitude")),
        longitude=_decimal_or_none(raw.get("Longitude")),
        founders=_parse_founders(raw),
        funding_rounds=_parse_funding_rounds(raw),
    )


def _parse_founders(raw: dict[str, str]) -> list[DealroomFounder]:
    names = split_semicolon(raw.get("Founders"))
    statuses = split_semicolon(raw.get("Founders statuses"))
    genders = split_semicolon(raw.get("Founders genders"))
    universities = split_semicolon(raw.get("Founders universities"))
    linkedin_urls = split_semicolon(raw.get("Founders linkedin"))
    backgrounds = split_semicolon(raw.get("Founders backgrounds"))

    founders: list[DealroomFounder] = []
    for index, name in enumerate(names):
        if name is None:
            continue
        founders.append(
            DealroomFounder(
                name=name,
                status=_at(statuses, index),
                gender=_at(genders, index),
                university=_at(universities, index),
                linkedin_url=_at(linkedin_urls, index),
                background=_at(backgrounds, index),
            )
        )
    return founders


def _parse_funding_rounds(raw: dict[str, str]) -> list[DealroomFundingRound]:
    round_types = split_semicolon(raw.get("Each round type"))
    amounts = split_semicolon(raw.get("Each round amount"))
    currencies = split_semicolon(raw.get("Each round currency"))
    dates = split_semicolon(raw.get("Each round date"))
    investors = split_semicolon(raw.get("Each round investors"))
    count = max(len(round_types), len(amounts), len(currencies), len(dates), len(investors))

    rounds: list[DealroomFundingRound] = []
    for index in range(count):
        round_type = _at(round_types, index)
        amount = _decimal_or_none(_at(amounts, index))
        currency = _at(currencies, index)
        date = _at(dates, index)
        investor_list = _clean_list((_at(investors, index) or "").split("++"))
        if round_type or amount is not None or currency or date or investor_list:
            rounds.append(
                DealroomFundingRound(
                    round_type=round_type,
                    amount=amount,
                    currency=currency,
                    date=date,
                    investors=investor_list,
                )
            )
    return rounds


def _at(values: list[str | None], index: int) -> str | None:
    return values[index] if index < len(values) else None


def _clean_list(values: Iterable[str | None]) -> list[str]:
    return [value for value in (_clean_value(value) for value in values) if value is not None]


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return None if cleaned.lower() in MISSING_VALUES else cleaned


def _decimal_or_none(value: str | None) -> Decimal | None:
    cleaned = _clean_value(value)
    if cleaned is None:
        return None
    try:
        return Decimal(cleaned.replace(",", ""))
    except InvalidOperation:
        return None
