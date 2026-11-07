
import os

from sqlalchemy import create_engine, URL
from sqlalchemy.orm import declarative_base, sessionmaker


# Select PostgreSQL when a password is configured.
# Otherwise, use SQLite by default.

postgres_password = os.getenv("CLOUDPULSE_DB_PASSWORD")

if postgres_password:
    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg",
        username="postgres",
        password=postgres_password,
        host="localhost",
        port=5432,
        database="cloudpulse"
    )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

    print("CloudPulse database: PostgreSQL")

else:
    DATABASE_URL = "sqlite:///./cloudpulse.db"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    print("CloudPulse database: SQLite")


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
