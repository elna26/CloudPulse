
import boto3
from moto import mock_aws

from main import CloudPulse


class CloudPulseMonitoring:

    def __init__(self):
        self.mock = mock_aws()
        self.mock.start()

        self.cloudwatch = boto3.client(
            "cloudwatch",
            region_name="us-east-1"
        )

    def publish_metric(self, metric_name, value):
        self.cloudwatch.put_metric_data(
            Namespace="CloudPulse",
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Unit": "Count"
                }
            ]
        )

        print(f"Metric published: {metric_name} = {value}")

    def publish_scheduler_metrics(self, scheduler):
        metrics = scheduler.metrics

        for metric_name, value in metrics.items():
            self.publish_metric(metric_name, value)

    def get_metrics(self):
        return self.cloudwatch.list_metrics(
            Namespace="CloudPulse"
        )

    def close(self):
        self.mock.stop()


if __name__ == "__main__":
    monitoring = CloudPulseMonitoring()

    try:
        scheduler = CloudPulse(
            max_retries=3,
            enable_delays=False
        )

        scheduler.add_job(
            name="Generate monthly report",
            priority=2,
            idempotency_key="monitor-job-001"
        )

        scheduler.add_job(
            name="Process customer data",
            priority=1,
            idempotency_key="monitor-job-002"
        )

        scheduler.process_all_jobs()

        # Publish actual scheduler metrics to simulated CloudWatch.
        monitoring.publish_scheduler_metrics(scheduler)

        response = monitoring.get_metrics()

        print("\nCloudPulse monitoring metrics:")

        for metric in response["Metrics"]:
            print(metric["MetricName"])

    finally:
        monitoring.close()
