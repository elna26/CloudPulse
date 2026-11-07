
import logging
import time
import socket
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal
from database_worker import process_database_job
from models import Job, WorkerMetric


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger("CloudPulse.BackgroundWorker")


# --------------------------------------------------
# WORKER CONFIGURATION
# --------------------------------------------------

WORKER_ID = f"{socket.gethostname()}-{uuid4().hex[:8]}"

POLL_INTERVAL = 3
STALE_JOB_TIMEOUT_SECONDS = 300

WORKER_STARTED_AT = datetime.now(timezone.utc)

worker_metrics = {
    "jobs_claimed": 0,
    "jobs_completed": 0,
    "jobs_failed": 0,
    "jobs_recovered": 0,
    "total_attempts": 0
}


# --------------------------------------------------
# GET WORKER METRICS
# --------------------------------------------------

def get_worker_metrics():

    return {
        "worker_id": WORKER_ID,
        **worker_metrics
    }


# --------------------------------------------------
# SAVE WORKER METRICS TO POSTGRESQL
# --------------------------------------------------

def save_worker_metrics(db, status="running"):

    record = WorkerMetric(
        worker_id=WORKER_ID,
        jobs_claimed=worker_metrics["jobs_claimed"],
        jobs_completed=worker_metrics["jobs_completed"],
        jobs_failed=worker_metrics["jobs_failed"],
        jobs_recovered=worker_metrics["jobs_recovered"],
        total_attempts=worker_metrics["total_attempts"],
        status=status,
        last_heartbeat=datetime.now(timezone.utc),
        started_at=WORKER_STARTED_AT,
        updated_at=datetime.now(timezone.utc)
    )

    db.merge(record)
    db.commit()


# --------------------------------------------------
# RECOVER ABANDONED JOBS
# --------------------------------------------------

def recover_abandoned_jobs(db):

    cutoff = datetime.now(timezone.utc) - timedelta(
        seconds=STALE_JOB_TIMEOUT_SECONDS
    )

    recovery = (
        update(Job)
        .where(
            Job.status == "processing",
            Job.locked_at.is_not(None),
            Job.locked_at < cutoff
        )
        .values(
            status="pending",
            locked_by=None,
            locked_at=None,
            updated_at=datetime.now(timezone.utc)
        )
    )

    result = db.execute(recovery)
    db.commit()

    recovered = result.rowcount or 0

    if recovered > 0:

        worker_metrics["jobs_recovered"] += recovered

        logger.warning(
            "Recovered %s abandoned job(s)",
            recovered
        )

    return recovered


# --------------------------------------------------
# FIND NEXT PENDING JOB
# --------------------------------------------------

def get_next_pending_job(db):

    return (
        db.query(Job)
        .filter(Job.status == "pending")
        .order_by(
            Job.priority.desc(),
            Job.created_at.asc()
        )
        .first()
    )


# --------------------------------------------------
# BACKGROUND WORKER
# --------------------------------------------------

def run_worker():

    logger.info("CloudPulse background worker started")
    logger.info("Worker ID: %s", WORKER_ID)

    try:

        with SessionLocal() as db:
            save_worker_metrics(db, status="running")

        while True:

            db = SessionLocal()

            try:

                recover_abandoned_jobs(db)

                # Update heartbeat and persist current metrics.
                save_worker_metrics(db, status="running")

                job = get_next_pending_job(db)

                if job is None:

                    logger.info("No pending jobs. Waiting...")

                    time.sleep(POLL_INTERVAL)
                    continue

                job_id = job.id

                logger.info(
                    "Found pending job: %s | Priority: %s",
                    job_id,
                    job.priority
                )

                try:

                    result = process_database_job(
                        db=db,
                        job_id=job_id,
                        worker_id=WORKER_ID
                    )

                    if result:

                        worker_metrics["jobs_claimed"] += 1

                        worker_metrics["total_attempts"] += (
                            result.get("attempts", 0)
                        )

                        if result.get("status") == "completed":

                            worker_metrics["jobs_completed"] += 1

                        elif result.get("status") == "failed":

                            worker_metrics["jobs_failed"] += 1

                    save_worker_metrics(db, status="running")

                    logger.info(
                        "Job processing result: %s",
                        result
                    )

                    logger.info(
                        "Worker metrics: %s",
                        get_worker_metrics()
                    )

                except ValueError as exc:

                    logger.warning(
                        "Job %s was not claimed: %s",
                        job_id,
                        exc
                    )

            except SQLAlchemyError:

                db.rollback()

                logger.exception(
                    "Database error in background worker"
                )

                time.sleep(POLL_INTERVAL)

            finally:

                db.close()

    except KeyboardInterrupt:

        logger.info("Background worker stopped safely")

        try:

            with SessionLocal() as db:

                save_worker_metrics(db, status="stopped")

        except SQLAlchemyError:

            logger.exception(
                "Could not save final worker metrics"
            )

        logger.info(
            "Final worker metrics: %s",
            get_worker_metrics()
        )


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    run_worker()
