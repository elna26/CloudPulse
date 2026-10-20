import unittest

from main import CloudPulse


class TestCloudPulseReliability(unittest.TestCase):

    def setUp(self):
        self.cloud = CloudPulse(
            max_retries=2,
            enable_delays=False
        )

    def test_duplicate_job_is_blocked(self):
        self.cloud.add_job("Order", 1, "order-1")
        result = self.cloud.add_job("Order", 1, "order-1")

        self.assertFalse(result)
        self.assertEqual(len(self.cloud.jobs), 1)
        self.assertEqual(
            self.cloud.metrics["duplicates_blocked"], 1
        )

    def test_priority_order(self):
        self.cloud.add_job("Low priority", 3, "low")
        self.cloud.add_job("High priority", 1, "high")
        self.cloud.add_job("Medium priority", 2, "medium")

        self.cloud.process_next_job()

        high_job = self.cloud.get_job(1)
        self.assertEqual(high_job["status"], "completed")

    def test_retry_eventually_succeeds(self):
        self.cloud.add_job(
            "Temporary failure", 1, "retry-1", fail_first_n=2
        )

        self.cloud.process_all_jobs()

        job = self.cloud.get_job(0)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["attempts"], 3)
        self.assertEqual(
            self.cloud.metrics["retries_scheduled"], 2
        )

    def test_retry_limit_marks_permanent_failure(self):
        self.cloud.add_job(
            "Persistent failure", 1, "failure-1", fail_first_n=10
        )

        self.cloud.process_all_jobs()

        job = self.cloud.get_job(0)
        self.assertEqual(job["status"], "permanently_failed")
        self.assertEqual(job["attempts"], 3)
        self.assertEqual(
            self.cloud.metrics["jobs_permanently_failed"], 1
        )

    def test_key_cannot_be_reused_for_different_job(self):
        self.cloud.add_job("Order", 1, "shared-key")

        with self.assertRaises(ValueError):
            self.cloud.add_job("Report", 2, "shared-key")

        self.assertEqual(len(self.cloud.jobs), 1)

    def test_metrics_track_completed_jobs(self):
        self.cloud.add_job("Order", 1, "order-2")
        self.cloud.process_all_jobs()

        self.assertEqual(self.cloud.metrics["jobs_submitted"], 1)
        self.assertEqual(self.cloud.metrics["jobs_completed"], 1)

    def test_get_job_status(self):
        self.cloud.add_job("Order", 1, "order-status")

        status = self.cloud.get_job_status(0)

        self.assertEqual(status, "pending")

    def test_get_missing_job_status(self):
        status = self.cloud.get_job_status(999)

        self.assertEqual(status, "not_found")

    def test_invalid_priority_is_rejected(self):
        with self.assertRaises(ValueError):
            self.cloud.add_job(
                "Invalid job", 1.5, "invalid-priority"
            )


if __name__ == "__main__":
    unittest.main()
