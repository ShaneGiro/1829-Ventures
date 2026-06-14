"""Rotate Ritchie's scoped API key.

Prints the new plaintext key once. The database stores only the SHA-256 hash.
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.constants import Role
from app.core.database import SyncSessionLocal
from app.core.security import generate_api_key, hash_api_key
from app.models.user import User
from app.services.auth_service import AGENT_EMAIL


def main() -> None:
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    with SyncSessionLocal() as session:
        user = session.scalar(select(User).where(User.email == AGENT_EMAIL))
        if user is None:
            user = User(
                email=AGENT_EMAIL,
                full_name="Ritchie",
                role=Role.AGENT,
                is_agent=True,
                is_active=True,
            )
            session.add(user)

        user.api_key_hash = api_key_hash
        user.is_agent = True
        user.role = Role.AGENT
        user.is_active = True
        session.commit()

    print(api_key)


if __name__ == "__main__":
    main()
