
from aws_monitoring import CloudPulseMonitoring
from main import CloudPulse


def test_cloudwatch_receives_scheduler_metrics():
    monitoring = CloudPulseMonitoring()

    try:
        scheduler = CloudPulse(
            max_retries=3,
            enable_delays=False
        )

        scheduler.add_job(
            name="Monitoring test job",
            priority=1,
            idempotency_key="monitor-test-001"
        )

        scheduler.process_all_jobs()

        monitoring.publish_scheduler_metrics(scheduler)

        response = monitoring.get_metrics()

        metric_names = [
            metric["MetricName"]
            for metric in response["Metrics"]
        ]

        assert "jobs_submitted" in metric_names
        assert "jobs_completed" in metric_names
        assert "failed_attempts" in metric_names

    finally:
        monitoring.close()
