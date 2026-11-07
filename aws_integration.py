
import json
import boto3
from moto import mock_aws


class CloudPulseSQS:

    def __init__(self):
        self.mock = mock_aws()
        self.mock.start()

        self.sqs = boto3.client(
            "sqs",
            region_name="us-east-1"
        )

        # Main job queue
        main_response = self.sqs.create_queue(
            QueueName="cloudpulse-jobs"
        )
        self.queue_url = main_response["QueueUrl"]

        # Dead Letter Queue
        dlq_response = self.sqs.create_queue(
            QueueName="cloudpulse-dlq"
        )
        self.dlq_url = dlq_response["QueueUrl"]

    def send_job(
        self,
        job_id,
        name,
        priority,
        idempotency_key=None,
        fail_first_n=0
    ):
        message = {
            "job_id": job_id,
            "name": name,
            "priority": priority,
            "idempotency_key": idempotency_key or str(job_id),
            "fail_first_n": fail_first_n
        }

        return self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(message)
        )

    def receive_jobs(self):
        return self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=10
        )

    def delete_job(self, receipt_handle):
        return self.sqs.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle
        )

    def send_dead_letter_job(self, job_data):
        return self.sqs.send_message(
            QueueUrl=self.dlq_url,
            MessageBody=json.dumps(job_data)
        )

    def receive_dead_letter_jobs(self):
        return self.sqs.receive_message(
            QueueUrl=self.dlq_url,
            MaxNumberOfMessages=10
        )

    def close(self):
        self.mock.stop()
