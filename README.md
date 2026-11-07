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

### Continuous Integration
- GitHub Actions workflow.
- Automatic test execution on pushes to `main`.
- Automatic test execution on pull requests targeting `main`.
- Python 3.11 test environment.

### Performance Benchmarking
- In-memory priority queue benchmarking.
- Tests with 1,000, 5,000, and 10,000 jobs.
- Five runs per workload.
- Median execution-time measurements.
- Submission and processing throughput measurements.

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
| GitHub Actions | Continuous integration |

## Project Structure

```text
CloudPulse/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── benchmarks/
│   └── benchmark_queue.py
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

```powershell
uvicorn api:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Database Configuration

CloudPulse supports SQLite by default and PostgreSQL when the PostgreSQL password environment