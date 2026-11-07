
import logging
import os
import hmac
from uuid import uuid4

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Query,
    Request
)
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from database import engine, get_db
from database_worker import process_database_job
import models


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger("CloudPulse.API")


# --------------------------------------------------
# API SECURITY
# --------------------------------------------------

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def require_api_key(api_key: str | None = Depends(api_key_header)):
    expected_key = os.getenv("CLOUDPULSE_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="API authentication is not configured."
        )

    if not api_key or not hmac.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key."
        )

    return True


# --------------------------------------------------
# APPLICATION INITIALIZATION
# --------------------------------------------------

app = FastAPI(
    title="CloudPulse API",
    description="""
# CloudPulse – Intelligent Job Queue System

A reliable job queue and failure recovery system.

Features:
- Job creation and management
- Priority-based scheduling
- Automatic retry and failure handling
- Idempotency protection
- Job filtering, sorting and pagination
- PostgreSQL and SQLite support
- Database-backed job processing
- Health monitoring
- Worker metrics and monitoring
- API key authentication
""",
    version="1.0.0",
    contact={"name": "CloudPulse Developer"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {
            "name": "System",
            "description": "Health monitoring and system information."
        },
        {
            "name": "Jobs",
            "description": "Create, retrieve, update, process and delete jobs."
        },
        {
            "name": "Workers",
            "description": "Background worker metrics and monitoring."
        }
    ]
)

models.Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# GLOBAL DATABASE ERROR HANDLER
# --------------------------------------------------

@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):

    logger.exception(
        "Database error while processing request: %s %s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "A database error occurred. Please try again later."
        }
    )


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class JobCreate(BaseModel):

    name: str = Field(min_length=1, max_length=200)

    priority: int = Field(default=1, ge=1, le=10)

    max_retries: int = Field(default=3, ge=0, le=10)

    fail_first_n: int = Field(default=0, ge=0, le=10)

    idempotency_key: str | None = Field(
        default=None,
        max_length=100
    )


class JobUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200
    )

    priority: int | None = Field(
        default=None,
        ge=1,
        le=10
    )

    max_retries: int | None = Field(
        default=None,
        ge=0,
        le=10
    )

    fail_first_n: int | None = Field(
        default=None,
        ge=0,
        le=10
    )


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/", tags=["System"])
def home():

    return {
        "message": "Welcome to CloudPulse API",
        "status": "running",
        "version": "1.0.0"
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):

    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "service": "CloudPulse",
            "database": "connected"
        }

    except SQLAlchemyError:

        db.rollback()

        logger.exception("Database health check failed.")

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "CloudPulse",
                "database": "disconnected"
            }
        )


# --------------------------------------------------
# WORKER METRICS
# --------------------------------------------------

@app.get(
    "/workers/metrics",
    tags=["Workers"],
    summary="Retrieve background worker metrics",
    dependencies=[Depends(require_api_key)]
)
def get_all_worker_metrics(db: Session = Depends(get_db)):

    workers = (
        db.query(models.WorkerMetric)
        .order_by(models.WorkerMetric.last_heartbeat.desc())
        .all()
    )

    return {
        "total_workers": len(workers),
        "workers": [
            {
                "worker_id": worker.worker_id,
                "status": worker.status,
                "jobs_claimed": worker.jobs_claimed,
                "jobs_completed": worker.jobs_completed,
                "jobs_failed": worker.jobs_failed,
                "jobs_recovered": worker.jobs_recovered,
                "total_attempts": worker.total_attempts,
                "last_heartbeat": worker.last_heartbeat,
                "started_at": worker.started_at,
                "updated_at": worker.updated_at
            }
            for worker in workers
        ]
    }


# --------------------------------------------------
# CREATE JOB
# --------------------------------------------------

@app.post(
    "/jobs",
    status_code=201,
    tags=["Jobs"],
    dependencies=[Depends(require_api_key)]
)
def create_job(job: JobCreate, db: Session = Depends(get_db)):

    if job.idempotency_key:

        existing_job = db.query(models.Job).filter(
            models.Job.idempotency_key == job.idempotency_key
        ).first()

        if existing_job:

            if (
                existing_job.name != job.name
                or existing_job.priority != job.priority
                or existing_job.max_retries != job.max_retries
                or existing_job.fail_first_n != job.fail_first_n
            ):

                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key reused for a different job."
                )

            return {
                "message": "Duplicate request: existing job returned",
                "job_id": existing_job.id,
                "name": existing_job.name,
                "status": existing_job.status
            }

    new_job = models.Job(
        name=job.name,
        priority=job.priority,
        max_retries=job.max_retries,
        fail_first_n=job.fail_first_n,
        idempotency_key=job.idempotency_key
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return {
        "message": "Job created successfully",
        "job_id": new_job.id,
        "name": new_job.name,
        "priority": new_job.priority,
        "status": new_job.status
    }


# --------------------------------------------------
# LIST, FILTER, PAGINATE AND SORT JOBS
# --------------------------------------------------

@app.get(
    "/jobs",
    tags=["Jobs"],
    dependencies=[Depends(require_api_key)]
)
def list_jobs(
    status: str | None = Query(default=None),
    priority: int | None = Query(default=None, ge=1, le=10),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(
        default="id",
        pattern="^(id|priority)$"
    ),
    order: str = Query(
        default="asc",
        pattern="^(asc|desc)$"
    ),
    db: Session = Depends(get_db)
):

    query = db.query(models.Job)

    if status:
        query = query.filter(models.Job.status == status)

    if priority is not None:
        query = query.filter(models.Job.priority == priority)

    total_jobs = query.count()

    sort_column = (
        models.Job.priority
        if sort_by == "priority"
        else models.Job.id
    )

    if order == "desc":
        query = query.order_by(
            sort_column.desc(),
            models.Job.id.asc()
        )
    else:
        query = query.order_by(
            sort_column.asc(),
            models.Job.id.asc()
        )

    jobs = query.offset(skip).limit(limit).all()

    return {
        "total_jobs": total_jobs,
        "skip": skip,
        "limit": limit,
        "sort_by": sort_by,
        "order": order,
        "jobs": [
            {
                "job_id": job.id,
                "name": job.name,
                "priority": job.priority,
                "status": job.status,
                "retries_used": job.retries_used
            }
            for job in jobs
        ]
    }


# --------------------------------------------------
# GET JOB BY ID
# --------------------------------------------------

@app.get(
    "/jobs/{job_id}",
    tags=["Jobs"],
    dependencies=[Depends(require_api_key)]
)
def get_job(job_id: int, db: Session = Depends(get_db)):

    job = db.query(models.Job).filter(
        models.Job.id == job_id
    ).first()

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    return {
        "job_id": job.id,
        "name": job.name,
        "priority": job.priority,
        "status": job.status,
        "max_retries": job.max_retries,
        "retries_used": job.retries_used,
        "attempts": job.attempts,
        "idempotency_key": job.idempotency_key,
        "locked_by": job.locked_by,
        "locked_at": job.locked_at,
        "last_error": job.last_error
    }


# --------------------------------------------------
# UPDATE JOB
# --------------------------------------------------

@app.put(
    "/jobs/{job_id}",
    tags=["Jobs"],
    dependencies=[Depends(require_api_key)]
)
def update_job(
    job_id: int,
    update: JobUpdate,
    db: Session = Depends(get_db)
):

    job = db.query(models.Job).filter(
        models.Job.id == job_id
    ).first()

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    if job.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot update job with status: {job.status}"
        )

    update_data = update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No update fields provided."
        )

    for field, value in update_data.items():
        if value is not None:
            setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return {
        "message": "Job updated successfully",
        "job_id": job.id,
        "name": job.name,
        "priority": job.priority,
        "max_retries": job.max_retries,
        "fail_first_n": job.fail_first_n,
        "status": job.status
    }


# --------------------------------------------------
# PROCESS JOB USING DATABASE WORKER
# --------------------------------------------------

@app.post(
    "/jobs/{job_id}/process",
    tags=["Jobs"],
    summary="Process a job using the database worker",
    dependencies=[Depends(require_api_key)]
)
def process_job(job_id: int, db: Session = Depends(get_db)):

    job = db.query(models.Job).filter(
        models.Job.id == job_id
    ).first()

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    if job.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Job cannot be processed from status: {job.status}"
        )

    worker_id = f"api-worker-{uuid4().hex[:8]}"

    try:

        result = process_database_job(
            db=db,
            job_id=job_id,
            worker_id=worker_id
        )

        return {
            "message": "Database worker processing finished",
            **result
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=409,
            detail=str(exc)
        )


# --------------------------------------------------
# DELETE JOB
# --------------------------------------------------

@app.delete(
    "/jobs/{job_id}",
    tags=["Jobs"],
    dependencies=[Depends(require_api_key)]
)
def delete_job(job_id: int, db: Session = Depends(get_db)):

    job = db.query(models.Job).filter(
        models.Job.id == job_id
    ).first()

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    db.delete(job)
    db.commit()

    return {
        "message": "Job deleted successfully",
        "job_id": job_id
    }
