"""Seed the two current funds (Beta and Fund I) and the default pipeline stages.

Idempotent: re-running will not create duplicates. Uses the sync engine.

    python -m scripts.seed_funds
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.constants import SEED_DEAL_STATUSES, FundStatus
from app.core.database import SyncSessionLocal
from app.models.deal_status import DealStatus
from app.models.fund import Fund

SEED_FUNDS: tuple[dict[str, object], ...] = (
    {"name": "Beta", "fund_number": "Beta", "status": FundStatus.ACTIVE},
    {"name": "Fund I", "fund_number": "I", "status": FundStatus.ACTIVE},
)


def seed() -> None:
    with SyncSessionLocal() as session:
        for fund_data in SEED_FUNDS:
            exists = session.scalar(select(Fund).where(Fund.name == fund_data["name"]))
            if not exists:
                session.add(Fund(**fund_data))
                print(f"[seed] created fund: {fund_data['name']}")
            else:
                print(f"[seed] fund exists: {fund_data['name']}")

        for order, name in enumerate(SEED_DEAL_STATUSES):
            exists = session.scalar(select(DealStatus).where(DealStatus.name == name))
            if not exists:
                session.add(
                    DealStatus(
                        name=name,
                        sort_order=order,
                        is_system=True,
                        is_terminal=(name == "Closed/Invested"),
                    )
                )
                print(f"[seed] created stage: {name}")
            else:
                print(f"[seed] stage exists: {name}")

        session.commit()
    print("[seed] done")


if __name__ == "__main__":
    seed()
