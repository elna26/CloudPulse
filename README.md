# CloudPulse

**A Reliable, Database-Backed Job Queue and Background Worker System**

CloudPulse is a Python-based job processing system designed to demonstrate reliable job scheduling, priority-based execution, retry handling, database persistence, worker concurrency, and monitoring.

The project combines FastAPI, SQLAlchemy, SQLite, PostgreSQL, background workers, and AWS service simulations using Moto.

## Features

### Job Processing
- Priority-based job scheduling.
- Job creation, retrieval, updating, and deletion.
- Automatic retry handling.
- Configurable maximum retry attempts.
- Idempotency protection to prevent duplicate jobs.
- Job status tracking.
- Simulated job failures for reliability testing.

### Database Support
- SQLite support for local development.
- PostgreSQL integration using SQLAlchemy and Psycopg.
- Persistent job records.
- Database-backed worker metrics.
- Database constraints and indexes.

### Background Workers
- Continuous job polling.
- Multiple worker execution.
- Atomic job claiming using conditional database updates.
- Prevention of multiple workers claiming the same pending job.
- Recovery of abandoned processing jobs.
- Worker heartbeat and status tracking.

### Monitoring and Observability
- Jobs claimed, completed, and failed.
- Retry and recovery tracking.
- Total processing attempts.
- Worker status and heartbeat timestamps.
- REST API endpoint for worker metrics.

### AWS Service Simulations
AWS-related components are tested locally using Moto mocks.

- Amazon SQS queue simulation.
- Dead-letter queue handling.
- AWS worker simulation.
- Lambda-style event handler.
- DynamoDB table simulation.
- CloudWatch metric simulation.

**Note:** These components demonstrate AWS integration concepts locally. They are not deployed to a live AWS account.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application |
| FastAPI | REST API |
| SQLAlchemy | Database ORM |
| SQLite | Local database |
| PostgreSQL | Persistent database |
| Psycopg | PostgreSQL connectivity |
| Boto3 | AWS SDK |
| Moto | AWS service mocking |
| Pytest | Automated testing |
| Uvicorn | API server |

## Project Structure

```text
CloudPulse/
│
├── api.py
├── main.py
├── models.py
├── database.py
├── database_postgres.py
├── database_worker.py
├── worker.py
│
├── aws_database.py
├── aws_dynamodb.py
├── aws_integration.py
├── aws_lambda.py
├── aws_monitoring.py
├── aws_queue.py
├── aws_worker.py
│
├── tests/
│   ├── test_cloudpppulse.py
│   ├── test_concurrency.py
│   ├── test_postgres.py
│   ├── test_aws_integration.py
│   ├── test_dlq.py
│   ├── test_dynamodb.py
│   ├── test_lambda.py
│   └── test_monitoring.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

Clone the repository:

```bash
git clone https://github.com/elna26/CloudPulse.git
cd CloudPulse
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running the API

Start the FastAPI server:

```bash
uvicorn api:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Database Configuration

CloudPulse supports SQLite by default and PostgreSQL when the PostgreSQL password environment variable is configured.

For PostgreSQL, set the password locally in PowerShell:

```powershell
$env:CLOUDPULSE_DB_PASSWORD = Read-Host "Enter PostgreSQL password"
```

Create the SQLAlchemy tables:

```powershell
python -c "from database import Base, engine; from models import Job, WorkerMetric; Base.metadata.create_all(bind=engine); print('Tables created successfully')"
```

The PostgreSQL server and `cloudpulse` database must already be configured.

Keep the password private. Do not commit credentials or `.env` files to GitHub.

## Running the Background Worker

Open a separate PowerShell terminal, activate the virtual environment, and configure the same PostgreSQL environment variable.

Run:

```powershell
python worker.py
```

The worker continuously checks for pending jobs, processes available work, updates metrics, and attempts to recover abandoned jobs.

Press `Ctrl + C` to stop the worker.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application information |
| GET | `/health` | Health check |
| POST | `/jobs` | Create a job |
| GET | `/jobs` | Retrieve jobs |
| GET | `/jobs/{job_id}` | Retrieve a specific job |
| PUT | `/jobs/{job_id}` | Update a job |
| POST | `/jobs/{job_id}/process` | Process a job |
| DELETE | `/jobs/{job_id}` | Delete a job |
| GET | `/workers/metrics` | Retrieve worker metrics |

## Running Tests

Run the complete test suite:

```powershell
python -m pytest -v
```

The project has **21 passing tests** in the verified development environment.

PostgreSQL-specific tests require PostgreSQL configuration. Tests that depend on PostgreSQL are skipped when the database password environment variable is not configured.

## Reliability Concepts Demonstrated

CloudPulse demonstrates several backend engineering concepts:

- Priority queues and job scheduling.
- Retry strategies and exponential backoff.
- Idempotent job creation.
- Relational database persistence.
- Atomic database updates.
- Concurrent worker execution.
- Abandoned job recovery.
- Worker metrics and monitoring.
- Mock-based AWS integration testing.

## Current Limitations

- AWS services are simulated locally using Moto rather than deployed to AWS.
- The worker recovery mechanism uses a fixed timeout and does not implement a renewable lease.
- The project does not currently provide production-grade distributed coordination or deployment infrastructure.

## Future Improvements

- Live AWS deployment.
- Docker containerization.
- CI/CD automation.
- Redis-based distributed coordination.
- Enhanced worker health monitoring.
- Production-grade job recovery and lease management.
- Cloud deployment and scalability improvements.

## Author

**CloudPulse — A Backend Engineering Project**

GitHub: https://github.com/elna26/CloudPulse
