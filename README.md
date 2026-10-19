
# CloudPulse

A Python-based cloud job processing prototype exploring
priority scheduling, retry logic, idempotency and reliability metrics.

## Features

- Priority-based job scheduling using a heap
- Simulated failure recovery with exponential backoff
- Idempotency keys to block duplicate submissions
- Job status tracking and operational metrics
- Automated reliability tests using unittest

## Technology Stack

- Python
- heapq and itertools
- unittest
- AWS integration planned

## Run Locally

```bash
python main.py
```

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## Current Limitations

- Jobs and idempotency records are stored in memory.
- Failures are simulated for demonstration.
- Jobs are not yet durable across application restarts.
- AWS integration is not yet implemented.

## Future Improvements

- AWS SQS for message queuing
- AWS Lambda for job processing
- DynamoDB for durable job and idempotency records
- CloudWatch for logging and monitoring
