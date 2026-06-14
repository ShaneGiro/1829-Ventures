"""Dealroom import service tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.core.constants import ImportRowStatus
from app.integrations.dealroom_csv import parse_dealroom_csv
from app.models.company import Company
from app.models.import_row import ImportRow
from app.services.dealroom_import_service import company_conflicts, summarize_rows


def test_company_conflicts_require_review_for_curated_differences() -> None:
    row = parse_dealroom_csv(
        """ID,Name,Dealroom URL,Website,Industries,Sub industries,HQ city
1,Acme,https://app.dealroom.co/companies/acme,https://acme.com,robotics,,Rochester
"""
    ).rows[0]
    company = Company(
        name="Acme",
        website="https://curated.example",
        sector="Other",
        city="Rochester",
    )

    conflicts = company_conflicts(company, row)

    assert conflicts["website"] == {
        "existing": "https://curated.example",
        "incoming": "https://acme.com",
        "resolution": "review_required",
    }
    assert conflicts["sector"]["incoming"] == "Intelligent Systems, AI & Cyber"
    assert "city" not in conflicts


def test_summarize_rows_counts_preview_and_commit_statuses() -> None:
    now = datetime.now(UTC)
    rows = [
        ImportRow(
            id=uuid.uuid4(),
            batch_id=uuid.uuid4(),
            row_number=1,
            status=ImportRowStatus.CREATED,
            raw_data={},
            field_provenance={},
            conflicts={},
            created_at=now,
            updated_at=now,
        ),
        ImportRow(
            id=uuid.uuid4(),
            batch_id=uuid.uuid4(),
            row_number=2,
            status=ImportRowStatus.CONFLICT,
            raw_data={},
            field_provenance={},
            conflicts={},
            created_at=now,
            updated_at=now,
        ),
        ImportRow(
            id=uuid.uuid4(),
            batch_id=uuid.uuid4(),
            row_number=3,
            status=ImportRowStatus.COMMITTED,
            raw_data={},
            field_provenance={},
            conflicts={},
            created_at=now,
            updated_at=now,
        ),
    ]

    assert summarize_rows(rows) == {
        "total": 3,
        "created": 1,
        "matched": 0,
        "conflict": 1,
        "skipped": 0,
        "committed": 1,
    }
