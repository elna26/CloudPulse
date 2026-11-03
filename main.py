
import heapq
import itertools
import logging
import time


# Configure structured application logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger("CloudPulse")


class CloudPulse:
    """A simple priority-based job queue with retry and recovery support."""

    def __init__(self, max_retries=3, enable_delays=True):
        if (
            not isinstance(max_retries, int)
            or isinstance(max_retries, bool)
            or max_retries < 0
        ):
            raise ValueError("max_retries must be a non-negative integer.")

        self.jobs = []
        self.job_counter = itertools.count()
        self.queue_counter = itertools.count()

        self.max_retries = max_retries
        self.enable_delays = enable_delays

        self.idempotency_keys = {}
        self.jobs_by_id = {}

        self.metrics = {
            "jobs_submitted": 0,
            "jobs_completed": 0,
            "failed_attempts": 0,
            "retries_scheduled": 0,
            "jobs_permanently_failed": 0,
            "duplicates_blocked": 0,
        }

        logger.info(
            "CloudPulse initialized (max_retries=%s, delays=%s)",
            max_retries,
            enable_delays,
        )

    def add_job(self, name, priority, idempotency_key, fail_first_n=0):
        """Validate, register and schedule a new job."""

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Job name must be a non-empty string.")

        if not isinstance(priority, int) or isinstance(priority, bool):
            raise ValueError("Priority must be an integer.")

        if (
            not isinstance(fail_first_n, int)
            or isinstance(fail_first_n, bool)
            or fail_first_n < 0
        ):
            raise ValueError("fail_first_n must be a non-negative integer.")

        if (
            not isinstance(idempotency_key, str)
            or not idempotency_key.strip()
        ):
            raise ValueError("A non-empty idempotency key is required.")

        request = (name, priority, fail_first_n)

        # Prevent duplicate submissions.
        if idempotency_key in self.idempotency_keys:
            if self.idempotency_keys[idempotency_key] == request:
                self.metrics["duplicates_blocked"] += 1
                logger.warning("Duplicate job blocked: %s", name)
                return False

            logger.error(
                "Idempotency key reused for a different request: %s",
                idempotency_key,
            )
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

        logger.info(
            "Job submitted: id=%s name=%s priority=%s",
            job_id,
            name,
            priority,
        )

        return True

    def _schedule(self, job):
        """Add a job to the priority queue."""

        queue_id = next(self.queue_counter)

        heapq.heappush(
            self.jobs,
            (job["priority"], queue_id, job),
        )

        logger.debug(
            "Job scheduled: id=%s priority=%s",
            job["id"],
            job["priority"],
        )

    def get_job(self, job_id):
        """Return a job record, or None if it does not exist."""

        return self.jobs_by_id.get(job_id)

    def get_job_status(self, job_id):
        """Return the job status or 'not_found' for an unknown ID."""

        job = self.get_job(job_id)

        if job is None:
            return "not_found"

        return job["status"]

    def process_next_job(self):
        """Process the next highest-priority job."""

        if not self.jobs:
            logger.info("No jobs available to process.")
            return None

        _, _, job = heapq.heappop(self.jobs)

        job["status"] = "processing"
        job["attempts"] += 1

        logger.info(
            "Processing job: id=%s name=%s attempt=%s",
            job["id"],
            job["name"],
            job["attempts"],
        )

        # Simulate predictable initial failures for testing.
        failed = job["attempts"] <= job["fail_first_n"]

        if not failed:
            job["status"] = "completed"
            self.metrics["jobs_completed"] += 1

            logger.info(
                "Job completed successfully: id=%s name=%s",
                job["id"],
                job["name"],
            )

            return job["status"]

        self.metrics["failed_attempts"] += 1

        logger.warning(
            "Job attempt failed: id=%s name=%s attempt=%s",
            job["id"],
            job["name"],
            job["attempts"],
        )

        retries_used = job["attempts"] - 1

        if retries_used < self.max_retries:
            delay = 2 ** retries_used

            job["status"] = "retrying"
            self.metrics["retries_scheduled"] += 1

            logger.info(
                "Retry scheduled: id=%s delay_seconds=%s",
                job["id"],
                delay,
            )

            if self.enable_delays:
                time.sleep(delay)

            self._schedule(job)

        else:
            job["status"] = "permanently_failed"
            self.metrics["jobs_permanently_failed"] += 1

            logger.error(
                "Retry limit reached: id=%s name=%s",
                job["id"],
                job["name"],
            )

        return job["status"]

    def process_all_jobs(self):
        """Process queued jobs until no jobs remain."""

        while self.jobs:
            self.process_next_job()

    def show_metrics(self):
        """Log aggregate metrics and current job statuses."""

        logger.info("CloudPulse metrics: %s", self.metrics)

        for job in self.jobs_by_id.values():
            logger.info(
                "Job status: id=%s name=%s status=%s attempts=%s",
                job["id"],
                job["name"],
                job["status"],
                job["attempts"],
            )


if __name__ == "__main__":
    cloud = CloudPulse(max_retries=3)

    cloud.add_job(
        "Process order",
        1,
        "order-1001",
        fail_first_n=2,
    )

    cloud.add_job(
        "Generate report",
        2,
        "report-2001",
    )

    cloud.add_job(
        "Sync payment",
        3,
        "payment-3001",
        fail_first_n=10,
    )

    # Demonstrate duplicate protection.
    cloud.add_job(
        "Process order",
        1,
        "order-1001",
        fail_first_n=2,
    )

    cloud.process_all_jobs()
    cloud.show_metrics()
