
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text

from database import engine, SessionLocal
from models import Job
from worker import recover_abandoned_jobs, get_worker_metrics


pytestmark = pytest.mark.skipif(
    not os.getenv("CLOUDPULSE_DB_PASSWORD"),
    reason="PostgreSQL is not configured"
)


def test_postgresql_engine_selected():
    assert engine.dialect.name == "postgresql"


def test_postgresql_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


def test_jobs_table_exists():
    inspector = inspect(engine)

    assert "jobs" in inspector.get_table_names()

    columns = {
        column["name"]
        for column in inspector.get_columns("jobs")
    }

    assert "id" in columns
    assert "name" in columns
    assert "status" in columns


def test_recover_abandoned_job():

    db = SessionLocal()
    job = None

    try:
        job = Job(
            name="Abandoned Job Recovery Test",
            priority=5,
            status="processing",
            locked_by="crashed-worker",
            locked_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            idempotency_key=f"recovery-test-{uuid4().hex}"
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        recovered_count = recover_abandoned_jobs(db)

        db.refresh(job)

        assert recovered_count >= 1
        assert job.status == "pending"
        assert job.locked_by is None
        assert job.locked_at is None

    finally:
        if job is not None:
            db.delete(job)
            db.commit()

        db.close()


def test_worker_metrics_structure():

    metrics = get_worker_metrics()

    assert "worker_id" in metrics
    assert "jobs_claimed" in metrics
    assert "jobs_completed" in metrics
    assert "jobs_failed" in metrics
    assert "jobs_recovered" in metrics
    assert "total_attempts" in metrics
