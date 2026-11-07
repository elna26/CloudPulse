
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text
)
from datetime import datetime, timezone

from database import Base


# --------------------------------------------------
# JOB MODEL
# --------------------------------------------------

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)

    priority = Column(Integer, default=1, nullable=False)

    status = Column(String(30), default="pending", nullable=False)

    retries_used = Column(Integer, default=0, nullable=False)

    max_retries = Column(Integer, default=3, nullable=False)

    attempts = Column(Integer, default=0, nullable=False)

    fail_first_n = Column(Integer, default=0, nullable=False)

    idempotency_key = Column(
        String(100),
        unique=True,
        nullable=True
    )

    locked_by = Column(String(100), nullable=True)

    locked_at = Column(DateTime(timezone=True), nullable=True)

    last_error = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# --------------------------------------------------
# WORKER METRICS MODEL
# --------------------------------------------------

class WorkerMetric(Base):
    __tablename__ = "worker_metrics"

    worker_id = Column(
        String(100),
        primary_key=True
    )

    jobs_claimed = Column(
        Integer,
        default=0,
        nullable=False
    )

    jobs_completed = Column(
        Integer,
        default=0,
        nullable=False
    )

    jobs_failed = Column(
        Integer,
        default=0,
        nullable=False
    )

    jobs_recovered = Column(
        Integer,
        default=0,
        nullable=False
    )

    total_attempts = Column(
        Integer,
        default=0,
        nullable=False
    )

    status = Column(
        String(30),
        default="starting",
        nullable=False
    )

    last_heartbeat = Column(
        DateTime(timezone=True),
        nullable=True
    )

    started_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
