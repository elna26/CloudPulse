
import os
from threading import Barrier
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from database import SessionLocal
from database_worker import process_database_job
from models import Job


pytestmark = pytest.mark.skipif(
    not os.getenv("CLOUDPULSE_DB_PASSWORD"),
    reason="PostgreSQL is not configured"
)


def test_two_workers_cannot_claim_same_job():

    # Create one pending job.
    db = SessionLocal()

    job = Job(
        name="Concurrent Claim Test",
        priority=10,
        status="pending",
        max_retries=0,
        fail_first_n=0,
        idempotency_key=f"concurrency-{uuid4().hex}"
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = job.id
    db.close()

    # Make both workers start claiming at the same time.
    barrier = Barrier(2)

    def attempt_claim(worker_id):

        session = SessionLocal()

        try:
            barrier.wait(timeout=10)

            return process_database_job(
                db=session,
                job_id=job_id,
                worker_id=worker_id
            )

        except ValueError:
            return "claim_rejected"

        finally:
            session.close()

    # Run two independent workers simultaneously.
    with ThreadPoolExecutor(max_workers=2) as executor:

        futures = [
            executor.submit(attempt_claim, "worker-A"),
            executor.submit(attempt_claim, "worker-B")
        ]

        results = [future.result(timeout=30) for future in futures]

    # Exactly one worker must complete the job.
    completed = [
        result for result in results
        if isinstance(result, dict)
        and result["status"] == "completed"
    ]

    rejected = [
        result for result in results
        if result == "claim_rejected"
    ]

    assert len(completed) == 1
    assert len(rejected) == 1

    # Verify the final database state.
    db = SessionLocal()

    try:
        final_job = db.query(Job).filter(
            Job.id == job_id
        ).first()

        assert final_job.status == "completed"
        assert final_job.attempts == 1
        assert final_job.locked_by is None

    finally:
        db.close()
