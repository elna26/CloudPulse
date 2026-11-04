# CloudPulse — Intelligent Job Queue System

CloudPulse is a Python-based job queue and failure recovery system designed to manage background jobs reliably through priority scheduling, automatic retries, idempotency protection and REST API integration.

The project explores backend engineering concepts including job scheduling, database persistence, API development, failure handling and automated testing.

## Features

- **Priority-Based Scheduling:** Schedule jobs according to priority.
- **Automatic Retry Handling:** Retry failed jobs with failure recovery logic.
- **Exponential Backoff:** Introduce delays between retry attempts.
- **Idempotency Protection:** Prevent duplicate job submissions using idempotency keys.
- **Job Management:** Create, retrieve, update, process and delete jobs.
- **Job Status Tracking:** Monitor job execution states.
- **Filtering and Sorting:** Search jobs using status and priority filters.
- **Pagination:** Retrieve job records in manageable batches.
- **Database Persistence:** Store job information using SQLite.
- **Health Monitoring:** Check API health.
- **REST API:** Interact with the system through FastAPI endpoints.
- **API Documentation:** Explore endpoints through interactive Swagger UI.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastAPI | REST API framework |
| SQLAlchemy | Database interaction |
| SQLite | Database persistence |
| Pydantic | Request validation |
| Pytest | Automated testing |
| Git and GitHub | Version control |

## Project Structure

```text
CloudPulse/
│
├── api.py
├── main.py
├── database.py
├── models.py
├── cloudpulse.db
├── requirements.txt
├── README.md
├── .gitignore
│
└── tests/
    └── test_cloudpppulse.py
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/elna26/CloudPulse.git
cd CloudPulse
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Run the Application

Start the FastAPI server:

```bash
python -m uvicorn api:app --reload
```

The application will run at:

`http://127.0.0.1:8000`

## API Documentation

Interactive Swagger documentation:

`http://127.0.0.1:8000/docs`

Alternative API documentation:

`http://127.0.0.1:8000/redoc`

## Available API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API welcome endpoint |
| GET | `/health` | Check API health |
| POST | `/jobs` | Create a job |
| GET | `/jobs` | List and search jobs |
| GET | `/jobs/{job_id}` | Retrieve a job |
| PUT | `/jobs/{job_id}` | Update a pending job |
| DELETE | `/jobs/{job_id}` | Delete a job |
| POST | `/jobs/{job_id}/process` | Process a job |

## Run Automated Tests

```bash
python -m pytest -v
```

Current verified result: **9 tests passed**.

## Current Limitations

- SQLite is currently used as the application database.
- Job processing and failure handling are implemented as a prototype.
- AWS services have not yet been integrated.
- Production deployment, distributed workers and advanced monitoring are future improvements.

## Planned Improvements

- AWS EC2 deployment
- AWS RDS integration
- Amazon DynamoDB for NoSQL storage
- Amazon CloudWatch monitoring
- Docker containerisation
- GitHub Actions CI/CD
- Redis caching
- Background workers and concurrency improvements
- Performance and load testing

## Learning Objectives

CloudPulse is an ongoing engineering project focused on developing practical experience with:

- Backend API development
- Database systems
- Job scheduling and reliability
- Debugging and troubleshooting
- Automated testing
- Git and GitHub workflows
- Cloud infrastructure and DevOps

## License

This project is licensed under the MIT License.
