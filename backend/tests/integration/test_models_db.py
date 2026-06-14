"""DB-backed model tests: relationships, cascades, soft delete, and seed funds."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import FundStatus, InvestmentStatus, RelationshipStatus
from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.deal import Deal
from app.models.fund import Fund
from app.models.person import Person
from app.models.rubric import Rubric

pytestmark = pytest.mark.integration


def test_company_minimal_create(db_session: Session) -> None:
    company = Company(name="Minimal Co")
    db_session.add(company)
    db_session.commit()
    assert company.id is not None
    assert company.relationship_status == RelationshipStatus.IDENTIFIED
    assert company.sector == "Other"


def test_company_contact_links_person(db_session: Session) -> None:
    company = Company(name="Linked Co")
    person = Person(full_name="Jane Founder")
    db_session.add_all([company, person])
    db_session.flush()
    link = CompanyContact(company_id=company.id, person_id=person.id, is_primary=True)
    db_session.add(link)
    db_session.commit()

    fetched = db_session.scalar(select(Company).where(Company.id == company.id))
    assert fetched is not None
    assert len(fetched.contacts) == 1
    assert fetched.contacts[0].person.full_name == "Jane Founder"


def test_deal_rubric_one_to_one_and_cascade(db_session: Session) -> None:
    company = Company(name="Deal Co")
    db_session.add(company)
    db_session.flush()
    deal = Deal(company_id=company.id, investment_status=InvestmentStatus.INITIAL_REVIEW)
    deal.rubric = Rubric(deal_id=uuid.uuid4(), commercial_technical_balance=4)
    db_session.add(deal)
    db_session.commit()

    deal_id = deal.id
    db_session.delete(deal)
    db_session.commit()
    # Rubric is cascade-deleted with its deal.
    assert db_session.scalar(select(Rubric).where(Rubric.deal_id == deal_id)) is None


def test_soft_delete_keeps_row(db_session: Session) -> None:
    from datetime import UTC, datetime

    company = Company(name="Archive Co")
    db_session.add(company)
    db_session.commit()
    company.archived_at = datetime.now(UTC)
    db_session.commit()

    fetched = db_session.scalar(select(Company).where(Company.id == company.id))
    assert fetched is not None
    assert fetched.is_archived is True


def test_seed_funds_idempotent(db_session: Session) -> None:
    for _ in range(2):
        for name in ("Beta", "Fund I"):
            if not db_session.scalar(select(Fund).where(Fund.name == name)):
                db_session.add(Fund(name=name, status=FundStatus.ACTIVE))
        db_session.commit()
    funds = db_session.scalars(select(Fund)).all()
    names = sorted(f.name for f in funds)
    assert names == ["Beta", "Fund I"]
