"""Dealroom CSV parser tests."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.integrations.dealroom_csv import (
    map_dealroom_sector,
    normalize_domain,
    parse_dealroom_csv,
    split_semicolon,
)


def test_real_dealroom_export_detects_metadata_and_header() -> None:
    csv_path = Path(__file__).resolve().parents[3] / "Dealroom Data (6.10.26).csv"
    parsed = parse_dealroom_csv(csv_path.read_bytes())

    assert parsed.header_row_number == 3
    assert len(parsed.metadata_rows) == 2
    assert parsed.headers[:4] == ["ID", "Name", "Dealroom URL", "Website"]
    assert parsed.rows[0].name == "Neros"
    assert parsed.rows[0].dealroom_id == "4936908"
    assert parsed.rows[0].latitude == Decimal("34.0536909")
    assert parsed.rows[0].longitude == Decimal("-118.242766")


def test_parallel_founder_arrays_preserve_index_meaning() -> None:
    csv_text = "\n".join(
        [
            "URL,Filters",
            "https://example.test,filter",
            (
                "ID,Name,Dealroom URL,Website,Industries,Sub industries,Founders,"
                "Founders statuses,Founders genders,Founders universities,Founders linkedin"
            ),
            (
                "1,Acme,https://app.dealroom.co/companies/acme,https://www.acme.com,"
                "robotics,,Jane Doe;John Roe,current;former,female;male,RIT;MIT,"
                "https://linkedin.test/jane;https://linkedin.test/john"
            ),
        ]
    )
    parsed = parse_dealroom_csv(csv_text)

    founders = parsed.rows[0].founders
    assert [founder.name for founder in founders] == ["Jane Doe", "John Roe"]
    assert founders[0].university == "RIT"
    assert founders[1].linkedin_url == "https://linkedin.test/john"


def test_parallel_funding_round_arrays_split_round_investors() -> None:
    csv_text = "\n".join(
        [
            (
                "ID,Name,Dealroom URL,Website,Industries,Sub industries,Each round type,"
                "Each round amount,Each round currency,Each round date,Each round investors"
            ),
            (
                "1,Acme,https://app.dealroom.co/companies/acme,acme.com,energy,,"
                "SEED;SERIES A,1.5;10,USD;USD,jan/2024;may/2025,"
                "Foo Ventures++Angel One;Bar Capital"
            ),
        ]
    )
    parsed = parse_dealroom_csv(csv_text)

    rounds = parsed.rows[0].funding_rounds
    assert rounds[0].amount == Decimal("1.5")
    assert rounds[0].investors == ["Foo Ventures", "Angel One"]
    assert rounds[1].round_type == "SERIES A"


def test_split_semicolon_preserves_empty_positions() -> None:
    assert split_semicolon("one;;n/a;four") == ["one", None, None, "four"]


def test_domain_and_sector_mapping() -> None:
    assert normalize_domain("https://www.example.com/path") == "example.com"
    assert map_dealroom_sector(["security", "robotics"], [])[0] == (
        "Intelligent Systems, AI & Cyber"
    )
    assert map_dealroom_sector(["advanced materials"], [])[1] == ["unmapped_dealroom_taxonomy"]
