
import logging
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

import models


logger = logging.getLogger("CloudPulse.Worker")


def process_database_job(
    db: Session,
    job_id: int,
    worker_id: str
):
    """Atomically claim and process a database-backed job."""

    try:
        now = datetime.now(timezone.utc)

        # Atomically claim the job.
        # Only one worker can change pending -> processing.
        claim = (
            update(models.Job)
            .where(
                models.Job.id == job_id,
                models.Job.status == "pending"
            )
            .values(
                status="processing",
                locked_by=worker_id,
                locked_at=now
            )
        )

        result = db.execute(claim)

        if result.rowcount != 1:
            db.rollback()

            job = db.query(models.Job).filter(
                models.Job.id == job_id
            ).first()

            if job is None:
                raise ValueError("Job not found.")

            raise ValueError(
                f"Job cannot be claimed. Current status: {job.status}"
            )

        db.commit()

        job = db.query(models.Job).filter(
            models.Job.id == job_id
        ).first()

        if job is None:
            raise ValueError("Job not found after claiming.")

        logger.info(
            "Worker %s claimed job %s",
            worker_id,
            job_id
        )

        max_attempts = job.max_retries + 1

        while job.attempts < max_attempts:

            job.attempts += 1

            logger.info(
                "Processing job %s: attempt %s",
                job_id,
                job.attempts
            )

            if job.attempts <= job.fail_first_n:

                job.last_error = (
                    f"Simulated failure on attempt {job.attempts}"
                )

                if job.attempts < max_attempts:
                    job.retries_used += 1

                db.commit()

                logger.warning(
                    "Job %s failed on attempt %s",
                    job_id,
                    job.attempts
                )

                continue

            job.status = "completed"
            job.last_error = None
            job.locked_by = None
            job.locked_at = None

            db.commit()
            db.refresh(job)

            logger.info(
                "Job %s completed by worker %s",
                job_id,
                worker_id
            )

            return {
                "job_id": job.id,
                "name": job.name,
                "status": job.status,
                "attempts": job.attempts,
                "retries_used": job.retries_used,
                "worker_id": worker_id
            }

        job.status = "failed"
        job.locked_by = None
        job.locked_at = None

        db.commit()
        db.refresh(job)

        logger.error(
            "Job %s permanently failed",
            job_id
        )

        return {
            "job_id": job.id,
            "name": job.name,
            "status": job.status,
            "attempts": job.attempts,
            "retries_used": job.retries_used,
            "worker_id": worker_id,
            "last_error": job.last_error
        }

    except Exception:

        db.rollback()

        logger.exception(
            "Worker %s failed while processing job %s",
            worker_id,
            job_id
        )

        raise
