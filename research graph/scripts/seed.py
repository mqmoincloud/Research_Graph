"""The starting accounts.

    uv run python -m scripts.seed

Signup only ever creates a plain "user", so the first admin cannot come from
the API - it has to be written here. That is the same reason CaseDesk seeds its
admin: /auth/register is admin-only, so without a seeded row nobody could ever
register anyone.

Running it twice is safe. It skips any email that already exists rather than
wiping the table, so a real password you set later is not thrown away.
"""

from app.database import localSession
from app.models import User
from app.security import hash_password

# Demo data, not a real deployment - one password for every seeded account.
SEED_PASSWORD = "password123"

# The domain has to be one EmailStr accepts. Reserved TLDs like .test are
# rejected by email-validator, and these accounts have to survive a real login.
ACCOUNTS = [
    {"name": "Admin", "email": "admin@prepgraph.example.com", "role": "admin"},
    {"name": "Qaisar", "email": "qaisar@prepgraph.example.com", "role": "user"},
]


def seed():
    db = localSession()
    try:
        created = []
        skipped = []

        for entry in ACCOUNTS:
            existing = db.query(User).filter(User.email == entry["email"]).first()

            if existing:
                skipped.append(entry["email"])
                continue

            db.add(User(
                name=entry["name"],
                email=entry["email"],
                role=entry["role"],
                password_hash=hash_password(SEED_PASSWORD),
            ))
            created.append(entry)

        db.commit()

        print("Seeded accounts")
        print(f"  created : {len(created)}")
        print(f"  skipped : {len(skipped)} (already there)")

        if created:
            print()
            print(f"Log in with any of these, the password is {SEED_PASSWORD} for all:")
            for entry in created:
                print(f"  {entry['email']:34s} {entry['role']}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
