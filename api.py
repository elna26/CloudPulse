
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import engine, get_db
from main import CloudPulse
import models


# --------------------------------------------------
# APPLICATION INITIALIZATION
# STEP 25: PROFESSIONAL API DOCUMENTATION
# --------------------------------------------------

app = FastAPI(
    title="CloudPulse API",
    description="""
# CloudPulse – Intelligent Job Queue System

CloudPulse is a reliable job queue and failure recovery system
designed to manage background jobs efficiently.

## Features

- Create and manage jobs
- Priority-based job scheduling
- Automatic retry and failure handling
- Idempotency protection
- Job filtering and sorting
- Pagination
- Database persistence
- Health monitoring
- REST API integration

## API Usage

Use these endpoints to create, retrieve, update, process
and delete jobs.

All API responses use JSON format.
""",
    version="1.0.0",
    contact={
        "name": "CloudPulse Developer"
    },
    license_info={
        "name": "MIT"
    },
    openapi_tags=[
        {
            "name": "System",
            "description": "Health monitoring and system information."
        },
        {
            "name": "Jobs",
            "description": "Create, retrieve, update, process and delete jobs."
        }
    ]
)

models.Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# GLOBAL DATABASE ERROR HANDLER
# STEP 24
# --------------------------------------------------

@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):

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
    """Request model for creating a new job."""

    name: str = Field(
        min_length=1,
        max_length=200,
        description="Name of the job.",
        examples=["Generate monthly report"]
    )

    priority: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Job priority from 1 to 10.",
        examples=[5]
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts.",
        examples=[3]
    )

    fail_first_n: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Number of initial attempts that should fail.",
        examples=[0]
    )

    idempotency_key: str | None = Field(
        default=None,
        max_length=100,
        description="Unique key to prevent duplicate job creation.",
        examples=["report-001"]
    )


class JobUpdate(BaseModel):
    """Request model for updating a pending job."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated job name."
    )

    priority: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Updated priority from 1 to 10."
    )

    max_retries: int | None = Field(
        default=None,
        ge=0,
        le=10,
        description="Updated maximum retry count."
    )

    fail_first_n: int | None = Field(
        default=None,
        ge=0,
        le=10,
        description="Updated number of initial failures."
    )


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get(
    "/",
    tags=["System"],
    summary="API welcome endpoint",
    description="Returns the CloudPulse API welcome message and version."
)
def home():
    return {
        "message": "Welcome to CloudPulse API",
        "status": "running",
        "version": "1.0.0"
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get(
    "/health",
    tags=["System"],
    summary="Check API health",
    description="Checks the CloudPulse API health status."
)
def health_check():
    return {
        "status": "healthy",
        "service": "CloudPulse",
        "database": "connected"
    }


# --------------------------------------------------
# CREATE JOB
# --------------------------------------------------

@app.post(
    "/jobs",
    status_code=201,
    tags=["Jobs"],
    summary="Create a new job",
    description="""
Creates a new job in the CloudPulse system.

Supports priority, retry configuration and idempotency
protection against duplicate requests.
""",
    responses={
        201: {"description": "Job created successfully."},
        409: {"description": "Idempotency key conflict."},
        422: {"description": "Invalid request data."},
        500: {"description": "Database error."}
    }
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
    summary="List and search jobs",
    description="""
Returns jobs with filtering, sorting and pagination.

Available sorting fields: id and priority.
Available sorting orders: asc and desc.

You can combine status and priority filters.
""",
    responses={
        200: {"description": "Jobs retrieved successfully."},
        422: {"description": "Invalid query parameters."},
        500: {"description": "Database error."}
    }
)
def list_jobs(
    status: str | None = Query(
        default=None,
        description="Filter jobs by status, such as pending or completed."
    ),
    priority: int | None = Query(
        default=None,
        ge=1,
        le=10,
        description="Filter jobs by priority from 1 to 10."
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of jobs to skip."
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of jobs to return."
    ),
    sort_by: str = Query(
        default="id",
        pattern="^(id|priority)$",
        description="Sort field: id or priority."
    ),
    order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sorting order: asc or desc."
    ),
    db: Session = Depends(get_db)
):

    query = db.query(models.Job)

    if status:
        query = query.filter(models.Job.status == status)

    if priority is not None:
        query = query.filter(models.Job.priority == priority)

    total_jobs = query.count()

    if sort_by == "priority":
        sort_column = models.Job.priority
    else:
        sort_column = models.Job.id

    if order == "desc":
        query = query.order_by(sort_column.desc(), models.Job.id.asc())
    else:
        query = query.order_by(sort_column.asc(), models.Job.id.asc())

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
    summary="Get a job by ID",
    description="Retrieves complete information about a specific job.",
    responses={
        200: {"description": "Job retrieved successfully."},
        404: {"description": "Job not found."},
        500: {"description": "Database error."}
    }
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
        "idempotency_key": job.idempotency_key
    }


# --------------------------------------------------
# UPDATE JOB
# --------------------------------------------------

@app.put(
    "/jobs/{job_id}",
    tags=["Jobs"],
    summary="Update a pending job",
    description="""
Updates job details.

Only pending jobs can be updated.
Provide at least one field to update.
""",
    responses={
        200: {"description": "Job updated successfully."},
        400: {"description": "No update fields provided."},
        404: {"description": "Job not found."},
        409: {"description": "Job is not pending."},
        422: {"description": "Invalid request data."},
        500: {"description": "Database error."}
    }
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
# PROCESS JOB
# --------------------------------------------------

@app.post(
    "/jobs/{job_id}/process",
    tags=["Jobs"],
    summary="Process a job",
    description="""
Processes a pending job using the CloudPulse job queue.

Returns the final job status and retry count.
""",
    responses={
        200: {"description": "Job processing finished."},
        404: {"description": "Job not found."},
        409: {"description": "Job cannot be processed."},
        500: {"description": "Database error."}
    }
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

    cloud = CloudPulse(
        max_retries=job.max_retries,
        enable_delays=False
    )

    key = job.idempotency_key or f"database-job-{job.id}"

    cloud.add_job(
        name=job.name,
        priority=job.priority,
        idempotency_key=key
    )

    cloud.process_all_jobs()

    processed_job = cloud.get_job(0)

    job.status = processed_job["status"]
    job.retries_used = processed_job["attempts"] - 1

    db.commit()
    db.refresh(job)

    return {
        "message": "Job processing finished",
        "job_id": job.id,
        "name": job.name,
        "status": job.status,
        "retries_used": job.retries_used
    }


# --------------------------------------------------
# DELETE JOB
# --------------------------------------------------

@app.delete(
    "/jobs/{job_id}",
    tags=["Jobs"],
    summary="Delete a job",
    description="Permanently deletes a job from the database.",
    responses={
        200: {"description": "Job deleted successfully."},
        404: {"description": "Job not found."},
        500: {"description": "Database error."}
    }
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
