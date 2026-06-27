"""
Optional upgrade path to Postgres.
To use this:
1. Ensure your DATABASE_URL is set to a Postgres URI (e.g. postgresql://user:password@localhost:5432/dbname)
2. Run this script to export from sqlite and import to Postgres (or just use pgloader).
Here we provide a basic script that copies data from the default sqlite DB to Postgres.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import LicenseKey, Base

def migrate():
    # 1. Connect to local sqlite
    sqlite_engine = create_engine("sqlite:///./licenses.db")
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SqliteSession()

    # 2. Connect to postgres
    pg_url = os.getenv("POSTGRES_URL")
    if not pg_url:
        print("Please set POSTGRES_URL environment variable.")
        return

    pg_engine = create_engine(pg_url)
    Base.metadata.create_all(bind=pg_engine)
    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    # 3. Copy data
    keys = sqlite_session.query(LicenseKey).all()
    count = 0
    for k in keys:
        # Check if exists
        existing = pg_session.query(LicenseKey).filter_by(key=k.key).first()
        if not existing:
            new_k = LicenseKey(
                key=k.key,
                tier=k.tier,
                active=k.active,
                created_at=k.created_at,
                email=k.email
            )
            pg_session.add(new_k)
            count += 1
    
    pg_session.commit()
    print(f"Successfully migrated {count} keys to Postgres.")

if __name__ == "__main__":
    migrate()
