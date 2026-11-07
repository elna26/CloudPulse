
import logging
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from main import CloudPulse

logging.disable(logging.CRITICAL)


def percentile(values, percent):
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percent / 100)
    return ordered[index]


def benchmark_queue(job_count):
    cloud = CloudPulse(max_retries=0, enable_delays=False)

    latencies = []

    tracemalloc.start()

    total_start = time.perf_counter()

    for i in range(job_count):
        start = time.perf_counter()

        cloud.add_job(
            name=f"Benchmark Job {i}",
            priority=(i % 10) + 1,
            idempotency_key=f"benchmark-{job_count}-{i}"
        )

        latencies.append(time.perf_counter() - start)

    submission_time = time.perf_counter() - total_start

    processing_start = time.perf_counter()
    cloud.process_all_jobs()
    processing_time = time.perf_counter() - processing_start

    total_time = time.perf_counter() - total_start

    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "submission": submission_time,
        "processing": processing_time,
        "total": total_time,
        "completed": cloud.metrics["jobs_completed"],
        "throughput": job_count / total_time if total_time else 0,
        "average_latency": statistics.mean(latencies) * 1000,
        "p50": percentile(latencies, 50) * 1000,
        "p95": percentile(latencies, 95) * 1000,
        "p99": percentile(latencies, 99) * 1000,
        "peak_memory": peak_memory / (1024 * 1024),
    }


def main():
    benchmark_queue(500)

    print("\nCLOUDPULSE ADVANCED PERFORMANCE BENCHMARK")
    print("5 runs per test | Median measurements")
    print("=" * 65)

    for size in [1000, 5000, 10000]:
        results = [benchmark_queue(size) for _ in range(5)]

        print(f"\nJobs tested:          {size:,}")
        print(f"Jobs completed:       {min(r['completed'] for r in results):,}")
        print(f"Median submission:    {statistics.median(r['submission'] for r in results):.6f}s")
        print(f"Median processing:    {statistics.median(r['processing'] for r in results):.6f}s")
        print(f"Median total:         {statistics.median(r['total'] for r in results):.6f}s")
        print(f"Throughput:           {statistics.median(r['throughput'] for r in results):,.2f} jobs/s")
        print(f"Average latency:      {statistics.median(r['average_latency'] for r in results):.4f} ms")
        print(f"P50 latency:          {statistics.median(r['p50'] for r in results):.4f} ms")
        print(f"P95 latency:          {statistics.median(r['p95'] for r in results):.4f} ms")
        print(f"P99 latency:          {statistics.median(r['p99'] for r in results):.4f} ms")
        print(f"Peak Python memory:   {statistics.median(r['peak_memory'] for r in results):.2f} MB")

    print("\nAdvanced benchmark completed successfully.")


if __name__ == "__main__":
    main()
