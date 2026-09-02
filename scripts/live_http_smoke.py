"""Non-destructive concurrent HTTP smoke test for the public PSB service."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import statistics
import time
import urllib.request


def request_once(url: str, timeout: float) -> dict:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
            return {"ok": response.status == 200, "status": response.status, "seconds": time.perf_counter() - started, "bytes": len(body), "error": ""}
    except Exception as exc:
        return {"ok": False, "status": 0, "seconds": time.perf_counter() - started, "bytes": 0, "error": type(exc).__name__}


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * pct)))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    urls = [f"{base}/_stcore/health" if i % 2 == 0 else f"{base}/" for i in range(args.requests)]
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(lambda url: request_once(url, args.timeout), urls))
    elapsed = time.perf_counter() - started
    durations = [item["seconds"] for item in results]
    report = {
        "requests": len(results), "concurrency": args.concurrency,
        "passed": sum(1 for item in results if item["ok"]),
        "failed": sum(1 for item in results if not item["ok"]),
        "wall_seconds": round(elapsed, 3),
        "requests_per_second": round(len(results) / elapsed, 3) if elapsed else 0,
        "latency_seconds": {"mean": round(statistics.fmean(durations), 3) if durations else 0, "p50": round(percentile(durations, 0.50), 3), "p95": round(percentile(durations, 0.95), 3), "max": round(max(durations), 3) if durations else 0},
        "statuses": {}, "errors": {},
    }
    for item in results:
        status = str(item["status"])
        report["statuses"][status] = report["statuses"].get(status, 0) + 1
        if item["error"]:
            report["errors"][item["error"]] = report["errors"].get(item["error"], 0) + 1
    print(json.dumps(report, indent=2))
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
