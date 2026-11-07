
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
            TableName="cloudpulse-job-metadata",
            KeySchema=[
                {
                    "AttributeName": "job_id",
                    "KeyType": "HASH"
                }
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "job_id",
                    "AttributeType": "S"
                }
            ],
            BillingMode="PAY_PER_REQUEST"
        )

    def save_job(self, job_id, name, priority, status="pending"):
        self.table.put_item(
            Item={
                "job_id": str(job_id),
                "name": name,
                "priority": priority,
                "status": status
            }
        )

    def get_job(self, job_id):
        response = self.table.get_item(
            Key={"job_id": str(job_id)}
        )

        return response.get("Item")

    def update_job_status(self, job_id, status):
        self.table.update_item(
            Key={"job_id": str(job_id)},
            UpdateExpression="SET #job_status = :status",
            ExpressionAttributeNames={
                "#job_status": "status"
            },
            ExpressionAttributeValues={
                ":status": status
            }
        )

    def close(self):
        self.mock.stop()


if __name__ == "__main__":

    database = CloudPulseDynamoDB()

    try:
        database.save_job(
            job_id=401,
            name="Generate monthly report",
            priority=2
        )

        print("Saved job:", database.get_job(401))

        database.update_job_status(401, "completed")

        print("Updated job:", database.get_job(401))

    finally:
        database.close()
