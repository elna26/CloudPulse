
import json

from main import CloudPulse
from aws_integration import CloudPulseSQS


class CloudPulseWorker:

    def __init__(self, queue):
        self.queue = queue
        self.scheduler = CloudPulse(
            max_retries=3,
            enable_delays=False
        )
        self.receipts = []

    def process_messages(self):
        response = self.queue.receive_jobs()

        for message in response.get("Messages", []):
            job_data = json.loads(message["Body"])

            added = self.scheduler.add_job(
                name=job_data["name"],
                priority=job_data["priority"],
                idempotency_key=job_data["idempotency_key"],
                fail_first_n=job_data["fail_first_n"]
            )

            if added:
                scheduler_id = max(self.scheduler.jobs_by_id.keys())
                print("Job submitted:", job_data["name"])

                self.receipts.append({
                    "receipt_handle": message["ReceiptHandle"],
                    "job_data": job_data,
                    "scheduler_id": scheduler_id
                })
            else:
                print("Duplicate job blocked:", job_data["name"])
                self.queue.delete_job(message["ReceiptHandle"])

    def process_scheduler(self):
        self.scheduler.process_all_jobs()
        self.scheduler.show_metrics()

        for item in self.receipts:
            job = self.scheduler.get_job(item["scheduler_id"])

            if job is None:
                continue

            receipt = item["receipt_handle"]

            if job["status"] == "completed":
                self.queue.delete_job(receipt)
                print("Completed job removed from main queue.")

            elif job["status"] == "permanently_failed":
                dead_letter_data = {
                    **item["job_data"],
                    "final_status": "permanently_failed",
                    "failure_reason": "retry_limit_exceeded",
                    "attempts": job["attempts"]
                }

                self.queue.send_dead_letter_job(dead_letter_data)
                self.queue.delete_job(receipt)

                print("Permanently failed job moved to DLQ.")

        self.receipts.clear()


if __name__ == "__main__":
    queue = CloudPulseSQS()

    try:
        worker = CloudPulseWorker(queue)

        # Test 1: Fails twice, then succeeds.
        queue.send_job(
            job_id=101,
            name="Generate monthly report",
            priority=2,
            idempotency_key="report-101",
            fail_first_n=2
        )

        # Test 2: Exceeds the retry limit.
        queue.send_job(
            job_id=102,
            name="Process failed payment",
            priority=3,
            idempotency_key="payment-102",
            fail_first_n=10
        )

        worker.process_messages()
        worker.process_scheduler()

        dlq_response = queue.receive_dead_letter_jobs()
        dlq_messages = dlq_response.get("Messages", [])

        print("\nDead Letter Queue results:")
        print("Number of permanently failed jobs:", len(dlq_messages))

        for message in dlq_messages:
            print(json.loads(message["Body"]))

    finally:
        queue.close()
