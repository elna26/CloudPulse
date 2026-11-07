
import logging
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from main import CloudPulse

logging.disable(logging.CRITICAL)


def benchmark_queue(job_count):
    cloud = CloudPulse(max_retries=0, enable_delays=False)

    start = time.perf_counter()

    for i in range(job_count):
        cloud.add_job(
            name=f"Benchmark Job {i}",
            priority=(i % 10) + 1,
            idempotency_key=f"benchmark-{job_count}-{i}"
        )

    submission_time = time.perf_counter() - start

    start = time.perf_counter()
    cloud.process_all_jobs()
    processing_time = time.perf_counter() - start

    return (
        submission_time,
        processing_time,
        cloud.metrics["jobs_completed"]
    )


def main():
    # Warm-up run.
    benchmark_queue(500)

    print("\nCLOUDPULSE PERFORMANCE BENCHMARK")
    print("5 runs per test | Median measurements")
    print("=" * 60)

    for size in [1000, 5000, 10000]:
        submission_times = []
        processing_times = []
        completed_counts = []

        for _ in range(5):
            submission, processing, completed = benchmark_queue(size)

            submission_times.append(submission)
            processing_times.append(processing)
            completed_counts.append(completed)

        median_submission = statistics.median(submission_times)
        median_processing = statistics.median(processing_times)

        total_time = median_submission + median_processing

        throughput = (
            size / median_processing
            if median_processing > 0 else 0
        )

        print(f"\nJobs tested:       {size:,}")
        print(f"Jobs completed:    {min(completed_counts):,}")
        print(f"Median submission: {median_submission:.6f} seconds")
        print(f"Median processing: {median_processing:.6f} seconds")
        print(f"Median total:      {total_time:.6f} seconds")
        print(f"Throughput:        {throughput:,.2f} jobs/second")

    print("\nBenchmark completed successfully.")


if __name__ == "__main__":
    main()
