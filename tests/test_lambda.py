
from aws_integration import CloudPulseSQS
from aws_lambda import sqs_to_lambda


def test_sqs_lambda_integration():
    queue = CloudPulseSQS()

    try:
        queue.send_job(
            job_id=301,
            name="Generate monthly report",
            priority=2
        )

        result = sqs_to_lambda(queue)

        assert result["statusCode"] == 200
        assert result["processed_count"] == 1
        assert result["jobs"][0]["job_id"] == 301

        # Confirm the message was deleted.
        remaining = queue.receive_jobs()
        assert "Messages" not in remaining

    finally:
        queue.close()
