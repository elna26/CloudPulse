
import heapq
import itertools
import time


class CloudPulse:
    def __init__(self, max_retries=3, enable_delays=True):
        self.jobs = []
        self.job_counter = itertools.count()
        self.max_retries = max_retries
        self.enable_delays = enable_delays

        # Track request keys and all submitted jobs.
        self.idempotency_keys = {}
        self.jobs_by_id = {}

        # Operational metrics.
        self.metrics = {
            "jobs_submitted": 0,
            "jobs_completed": 0,
            "failed_attempts": 0,
            "retries_scheduled": 0,
            "jobs_permanently_failed": 0,
            "duplicates_blocked": 0,
        }

    def add_job(self, name, priority, idempotency_key,
                fail_first_n=0):
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise ValueError("Priority must be an integer.")

        if not isinstance(fail_first_n, int) or fail_first_n < 0:
            raise ValueError("fail_first_n must be non-negative.")

        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise ValueError("A non-empty idempotency key is required.")

        request = (name, priority, fail_first_n)

        if idempotency_key in self.idempotency_keys:
            if self.idempotency_keys[idempotency_key] == request:
                self.metrics["duplicates_blocked"] += 1
                print(f"DUPLICATE BLOCKED: {name}")
                return False

            raise ValueError(
                "Idempotency key reused for a different request."
            )

        job_id = next(self.job_counter)

        job = {
            "id": job_id,
            "name": name,
            "priority": priority,
            "attempts": 0,
            "fail_first_n": fail_first_n,
            "status": "pending",
            "idempotency_key": idempotency_key,
        }

        self.idempotency_keys[idempotency_key] = request
        self.jobs_by_id[job_id] = job
        self.metrics["jobs_submitted"] += 1
        self._schedule(job)

        print(f"Added job #{job_id}: {name}")
        return True

    def _schedule(self, job):
        queue_id = next(self.job_counter)
        heapq.heappush(
            self.jobs,
            (job["priority"], queue_id, job)
        )

    def get_job(self, job_id):
        """Return the current record for a job."""
        return self.jobs_by_id.get(job_id)

    def process_next_job(self):
        if not self.jobs:
            print("No jobs available.")
            return None

        _, _, job = heapq.heappop(self.jobs)
        job["status"] = "processing"
        job["attempts"] += 1

        print(
            f"\nProcessing {job['name']} "
            f"(attempt {job['attempts']})"
        )

        # Deterministic failure simulation for testing.
        failed = job["attempts"] <= job["fail_first_n"]

        if not failed:
            job["status"] = "completed"
            self.metrics["jobs_completed"] += 1
            print(f"SUCCESS: {job['name']} completed.")
            return job["status"]

        self.metrics["failed_attempts"] += 1
        print(f"FAILED: {job['name']} encountered an error.")

        retries_used = job["attempts"] - 1

        if retries_used < self.max_retries:
            delay = 2 ** retries_used
            job["status"] = "retrying"
            self.metrics["retries_scheduled"] += 1

            print(f"Retry scheduled after {delay} second(s).")

            if self.enable_delays:
                time.sleep(delay)

            self._schedule(job)
        else:
            job["status"] = "permanently_failed"
            self.metrics["jobs_permanently_failed"] += 1
            print(f"RETRY LIMIT REACHED: {job['name']}")

        return job["status"]

    def process_all_jobs(self):
        while self.jobs:
            self.process_next_job()

    def show_metrics(self):
        print("\n--- CloudPulse Metrics ---")
        for name, value in self.metrics.items():
            print(f"{name}: {value}")

        print("\n--- Job Status ---")
        for job in self.jobs_by_id.values():
            print(
                f"#{job['id']} {job['name']}: "
                f"{job['status']} "
                f"(attempts: {job['attempts']})"
            )


if __name__ == "__main__":
    cloud = CloudPulse(max_retries=3)

    cloud.add_job(
        "Process order", 1, "order-1001", fail_first_n=2
    )
    cloud.add_job(
        "Generate report", 2, "report-2001"
    )
    cloud.add_job(
        "Sync payment", 3, "payment-3001", fail_first_n=10
    )

    # Demonstrate duplicate protection.
    cloud.add_job(
        "Process order", 1, "order-1001", fail_first_n=2
    )

    cloud.process_all_jobs()
    cloud.show_metrics()
