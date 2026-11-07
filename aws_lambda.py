
import json

from aws_integration import CloudPulseSQS


def lambda_handler(event, context=None):
    """Simulate an AWS Lambda function triggered by SQS."""

    processed_jobs = []

    for record in event.get("Records", []):
        job_data = json.loads(record["body"])

        result = {
            "job_id": job_data["job_id"],
            "name": job_data["name"],
            "priority": job_data["priority"],
            "status": "received_by_lambda"
        }

        processed_jobs.append(result)

        print("Lambda processed:", result)

    return {
        "statusCode": 200,
        "processed_count": len(processed_jobs),
        "jobs": processed_jobs
    }


def sqs_to_lambda(queue):
    """Read SQS messages and pass them to the Lambda handler."""

    response = queue.receive_jobs()
    messages = response.get("Messages", [])

    event = {
        "Records": [
            {"body": message["Body"]}
            for message in messages
        ]
    }

    result = lambda_handler(event)

    # Delete messages after successful processing.
    for message in messages:
        queue.delete_job(message["ReceiptHandle"])

    return result


if __name__ == "__main__":

    queue = CloudPulseSQS()

    try:
        queue.send_job(
            job_id=301,
            name="Generate monthly report",
            priority=2
        )

        response = sqs_to_lambda(queue)

        print("\nLambda response:")
        print(json.dumps(response, indent=4))

    finally:
        queue.close()
