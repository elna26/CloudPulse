
import json

from aws_integration import CloudPulseSQS
from aws_worker import CloudPulseWorker


def test_permanently_failed_job_moves_to_dlq():
    queue = CloudPulseSQS()

    try:
        worker = CloudPulseWorker(queue)

        queue.send_job(
            job_id=201,
            name="Test failed job",
            priority=1,
            idempotency_key="test-201",
            fail_first_n=10
        )

        worker.process_messages()
        worker.process_scheduler()

        # Verify the job permanently failed.
        assert worker.scheduler.get_job_status(0) == "permanently_failed"

        # Verify the job reached the DLQ.
        response = queue.receive_dead_letter_jobs()
        messages = response.get("Messages", [])

        assert len(messages) == 1

        dlq_job = json.loads(messages[0]["Body"])

        assert dlq_job["job_id"] == 201
        assert dlq_job["final_status"] == "permanently_failed"
        assert dlq_job["attempts"] == 4
        assert dlq_job["failure_reason"] == "retry_limit_exceeded"

    finally:
        queue.close()
