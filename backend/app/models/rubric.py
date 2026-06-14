"""Rubric model: 1829 screening rubric for a deal opportunity.

Four binary knockout gates must all pass before weighted scoring counts. Fifteen
sub-scores (1-5) are stored individually; the composite (out of 100) is computed
by the diligence service from the weighted category rollups — see
core.constants.RUBRIC_CATEGORIES / RUBRIC_SUBSCORES. Rubric score writes are
blocked for Ritchie by default.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.deal import Deal


def _subscore() -> Mapped[int | None]:
    # 1-5 when set; NULL until scored. Range enforced in the service/schema layer.
    return mapped_column(Integer, nullable=True)


class Rubric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rubrics"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("deals.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # ─── Knockout gates (binary; all must pass) ──────────────────────────────
    gate_rit_connection: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    gate_thesis_alignment: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    gate_stage_seed_to_series_a: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    gate_tech_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # ─── Team (×5) ───────────────────────────────────────────────────────────
    commercial_technical_balance: Mapped[int | None] = _subscore()
    coachability_grit: Mapped[int | None] = _subscore()
    talent_magnetism: Mapped[int | None] = _subscore()

    # ─── Tech (×4) ───────────────────────────────────────────────────────────
    ip_protection: Mapped[int | None] = _subscore()
    external_validation: Mapped[int | None] = _subscore()
    development_stage: Mapped[int | None] = _subscore()

    # ─── Commercial (×5) ─────────────────────────────────────────────────────
    capital_efficiency: Mapped[int | None] = _subscore()
    path_to_revenue: Mapped[int | None] = _subscore()
    market_pain: Mapped[int | None] = _subscore()
    unit_economics: Mapped[int | None] = _subscore()

    # ─── RIT Fit (×4) ────────────────────────────────────────────────────────
    structural_advantage: Mapped[int | None] = _subscore()
    talent_pipeline: Mapped[int | None] = _subscore()
    mission_alignment: Mapped[int | None] = _subscore()

    # ─── Deal Dynamics (×2) ──────────────────────────────────────────────────
    syndicate_strength: Mapped[int | None] = _subscore()
    valuation_discipline: Mapped[int | None] = _subscore()

    # Computed composite (out of 100), recalculated by the diligence service.
    composite_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="rubric")

    def __repr__(self) -> str:
        return f"<Rubric deal={self.deal_id} composite={self.composite_score}>"
