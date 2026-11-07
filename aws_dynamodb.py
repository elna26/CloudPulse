
import boto3
from moto import mock_aws


class CloudPulseDynamoDB:

    def __init__(self):
        self.mock = mock_aws()
        self.mock.start()

        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name="us-east-1"
        )

        self.table = self.dynamodb.create_table(
            TableName="CloudPulseJobs",
            KeySchema=[
                {"AttributeName": "job_id", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "job_id", "AttributeType": "N"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

    def save_job(self, job_id, name, priority, status):
        self.table.put_item(
            Item={
                "job_id": job_id,
                "name": name,
                "priority": priority,
                "status": status
            }
        )

        print("Job saved:", job_id)

    def get_job(self, job_id):
        response = self.table.get_item(
            Key={"job_id": job_id}
        )

        return response.get("Item")

    def close(self):
        self.mock.stop()


if __name__ == "__main__":
    database = CloudPulseDynamoDB()

    try:
        database.save_job(
            job_id=401,
            name="Generate monthly report",
            priority=2,
            status="pending"
        )

        job = database.get_job(401)

        print("\nRetrieved job:")
        print(job)

    finally:
        database.close()
