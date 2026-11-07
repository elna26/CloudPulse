import boto3
from moto import mock_aws


@mock_aws
def test_sqs_queue():
    # Connect to simulated AWS SQS
    sqs = boto3.client(
        "sqs",
        region_name="us-east-1"
    )

    # Create a queue
    response = sqs.create_queue(
        QueueName="cloudpulse-jobs"
    )

    queue_url = response["QueueUrl"]

    # Send a job message
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody="Process CloudPulse job 101"
    )

    # Receive the message
    messages = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1
    )

    print("Queue created successfully!")
    print("Queue URL:", queue_url)
    print("Received message:", messages["Messages"][0]["Body"])


if __name__ == "__main__":
    test_sqs_queue()