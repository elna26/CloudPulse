
from aws_dynamodb import CloudPulseDynamoDB


def test_dynamodb_save_and_retrieve_job():
    database = CloudPulseDynamoDB()

    try:
        database.save_job(
            job_id=501,
            name="Test CloudPulse job",
            priority=3,
            status="pending"
        )

        job = database.get_job(501)

        assert job is not None
        assert job["job_id"] == 501
        assert job["name"] == "Test CloudPulse job"
        assert job["priority"] == 3
        assert job["status"] == "pending"

    finally:
        database.close()


def test_dynamodb_missing_job():
    database = CloudPulseDynamoDB()

    try:
        job = database.get_job(999)

        assert job is None

    finally:
        database.close()
