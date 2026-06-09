from __future__ import annotations

import argparse
import statistics
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple VecSeek retrieval benchmark.")
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--folder", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    timings = []
    payload = {"folder_name": args.folder, "query": args.query, "top_k": args.top_k}
    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        for _ in range(args.runs):
            started = time.perf_counter()
            response = client.post("/retrieve", json=payload)
            response.raise_for_status()
            timings.append(time.perf_counter() - started)

    print(f"runs={len(timings)}")
    print(f"avg_seconds={statistics.mean(timings):.4f}")
    print(f"p95_seconds={sorted(timings)[max(0, int(len(timings) * 0.95) - 1)]:.4f}")


if __name__ == "__main__":
    main()
