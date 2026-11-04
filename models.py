
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone

from database import Base


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
    idempotency_key = Column(String(100), unique=True, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
