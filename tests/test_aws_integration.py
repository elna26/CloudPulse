from aws_integration import CloudPulseSQS


def test_sqs_send_and_receive():
    queue = CloudPulseSQS()

    try:
        queue.send_job(
            job_id=101,
            name="Generate monthly report",
            priority=5
        )

        response = queue.receive_jobs()

        assert "Messages" in response
        assert len(response["Messages"]) == 1

        print("SQS integration successful!")
        print(response["Messages"][0]["Body"])

    finally:
        queue.close()