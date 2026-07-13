"""Explainable, versioned outreach-candidate ranking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AlumniFounderStatus, FollowUpStatus, OperationalStatus
from app.models.company import Company
from app.models.interaction import Interaction
from app.repositories import companies as company_repo
from app.repositories import interactions as interaction_repo
from app.repositories.companies import CompanyFilters
from app.schemas.company import CompanyRead
from app.schemas.outreach_candidate import CandidateScoreBreakdown, OutreachCandidateRead

SCORE_VERSION = "v1.3.1"
OUTREACH_COOLDOWN_DAYS = 30
TARGET_STAGES = frozenset(
    {"pre-seed", "pre seed", "seed", "series a", "early stage", "early-stage"}
)


@dataclass(frozen=True)
class CandidateScore:
    total: float
    breakdown: CandidateScoreBreakdown
    why: str
    warnings: list[str]


def _bounded(value: float | None, default: float = 0.0) -> float:
    return min(max(value if value is not None else default, 0.0), 1.0)


def score_candidate(company: Company, *, recently_contacted: bool) -> CandidateScore:
    """Score a company using tunable, explainable v1.3 weights."""
    warnings: list[str] = []
    alumni_confidence = _bounded(company.alumni_founder_confidence, 0.35)
    operational_confidence = _bounded(company.operational_confidence, 0.35)

    alumni = {
        AlumniFounderStatus.ACTIVE: 25 * alumni_confidence,
        AlumniFounderStatus.UNCLEAR: 12.5 * alumni_confidence,
        AlumniFounderStatus.UNVERIFIED: 5.0,
    }.get(company.alumni_founder_status, 0.0)
    operational = {
        OperationalStatus.OPERATIONAL: 25 * operational_confidence,
        OperationalStatus.UNCLEAR: 12.5 * operational_confidence,
        OperationalStatus.UNVERIFIED: 5.0,
    }.get(company.operational_status, 0.0)
    stage_fit = 15.0 if (company.stage or "").strip().lower() in TARGET_STAGES else 0.0
    rubric_fit = _bounded(company.rubric_fit_score and company.rubric_fit_score / 100) * 12.5
    thesis_alignment = (
        _bounded(company.thesis_alignment_score and company.thesis_alignment_score / 100) * 10.0
    )
    evidence_confidence = ((alumni_confidence + operational_confidence) / 2) * 7.5
    outreach_recency = 0.0 if recently_contacted else 5.0

    if company.alumni_founder_status == AlumniFounderStatus.UNVERIFIED:
        warnings.append("RIT alumni founder needs verification")
    elif company.alumni_founder_status == AlumniFounderStatus.UNCLEAR:
        warnings.append("RIT alumni founder evidence is unclear")
    if company.operational_status == OperationalStatus.UNVERIFIED:
        warnings.append("Operational status needs verification")
    elif company.operational_status == OperationalStatus.UNCLEAR:
        warnings.append("Operational evidence is unclear")
    if stage_fit == 0:
        warnings.append("Funding stage is outside or missing from the target range")
    if recently_contacted:
        warnings.append(f"Contacted within the last {OUTREACH_COOLDOWN_DAYS} days")
    if company.rubric_fit_score is None or company.thesis_alignment_score is None:
        warnings.append("1829 fit scoring is incomplete")

    breakdown = CandidateScoreBreakdown(
        alumni_founder=round(alumni, 2),
        operational=round(operational, 2),
        stage_fit=stage_fit,
        rubric_fit=round(rubric_fit, 2),
        thesis_alignment=round(thesis_alignment, 2),
        evidence_confidence=round(evidence_confidence, 2),
        outreach_recency=outreach_recency,
    )
    total = round(sum(breakdown.model_dump().values()), 2)
    positives = list(company.fit_score_reasons[:2])
    if company.alumni_founder_status == AlumniFounderStatus.ACTIVE:
        positives.append("active RIT alumni founder")
    if company.operational_status == OperationalStatus.OPERATIONAL:
        positives.append("current operational evidence")
    if stage_fit:
        positives.append("target funding stage")
    why = "; ".join(positives[:3]) or "Candidate needs additional verification and fit evidence."
    return CandidateScore(total=total, breakdown=breakdown, why=why, warnings=warnings)


async def list_candidates(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    include_recently_contacted: bool = False,
) -> tuple[list[OutreachCandidateRead], int]:
    companies = await company_repo.list_companies(
        session,
        limit=1000,
        offset=0,
        filters=CompanyFilters(relationship_statuses=("identified", "contacted", "nurture")),
    )
    interactions = await interaction_repo.list_interactions(
        session, limit=10000, offset=0, direction="outbound"
    )
    latest_by_company: dict[object, Interaction] = {}
    for interaction in interactions:
        if interaction.company_id is None:
            continue
        latest_by_company.setdefault(interaction.company_id, interaction)

    cutoff = datetime.now(UTC) - timedelta(days=OUTREACH_COOLDOWN_DAYS)
    candidates: list[OutreachCandidateRead] = []
    for company in companies:
        last = latest_by_company.get(company.id)
        last_at = (last.occurred_at or last.created_at) if last else None
        recently_contacted = bool(last_at and last_at >= cutoff)
        follow_up_needed = bool(last and last.follow_up_status == FollowUpStatus.NEEDED)
        if recently_contacted and not include_recently_contacted and not follow_up_needed:
            continue
        if company.alumni_founder_status in {
            AlumniFounderStatus.INACTIVE,
            AlumniFounderStatus.NOT_FOUND,
        }:
            continue
        if company.operational_status == OperationalStatus.NOT_OPERATIONAL:
            continue
        score = score_candidate(company, recently_contacted=recently_contacted)
        candidates.append(
            OutreachCandidateRead(
                company=CompanyRead.model_validate(company),
                score=score.total,
                score_version=SCORE_VERSION,
                breakdown=score.breakdown,
                why_this_company=score.why,
                warnings=score.warnings,
                last_outreach_at=last_at,
                follow_up_needed=follow_up_needed,
            )
        )
    candidates.sort(key=lambda item: (-item.score, item.company.name.lower()))
    return candidates[offset : offset + limit], len(candidates)
