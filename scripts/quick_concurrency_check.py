import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.utils.image_codec import encode_file_to_base64

API_URL = "http://127.0.0.1:8000/api/predict"
IMAGE_PATH = Path("samples/image_phone.jpeg")
IMAGE_B64 = encode_file_to_base64(IMAGE_PATH)

CONCURRENCY_LEVELS = [1, 2, 4, 8]
REQUESTS_PER_LEVEL = 16
TIMEOUT_SECONDS = 60


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((p / 100.0) * (len(ordered) - 1)))
    return ordered[index]


def one_request() -> dict:
    payload = {
        "uuid": str(uuid.uuid4()),
        "image": IMAGE_B64,
    }

    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()

    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
            elapsed_ms = (time.perf_counter() - started) * 1000

            return {
                "ok": True,
                "status": response.status,
                "elapsed_ms": elapsed_ms,
                "count": body.get("count", -1),
            }

    except HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "error": f"HTTPError: {exc.reason}",
        }

    except URLError as exc:
        return {
            "ok": False,
            "status": None,
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "error": f"URLError: {exc.reason}",
        }

    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "error": repr(exc),
        }


def run_level(concurrency: int) -> None:
    started = time.perf_counter()
    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(one_request) for _ in range(REQUESTS_PER_LEVEL)]
        for future in as_completed(futures):
            results.append(future.result())

    duration_s = time.perf_counter() - started
    successes = [r for r in results if r["ok"]]
    failures = [r for r in results if not r["ok"]]
    latencies = [r["elapsed_ms"] for r in successes]
    qps = len(successes) / duration_s if duration_s > 0 else 0.0

    print(f"\n=== concurrency={concurrency} ===")
    print(f"requests={len(results)}, ok={len(successes)}, failed={len(failures)}")
    print(f"batch_duration_s={duration_s:.3f}, approx_qps={qps:.2f}")

    if latencies:
        print(f"avg_ms={sum(latencies) / len(latencies):.2f}")
        print(f"p95_ms={percentile(latencies, 95):.2f}")
        print(f"max_ms={max(latencies):.2f}")

    if failures:
        for failure in failures[:3]:
            print("sample_failure =", failure)


def main() -> None:
    print(f"API_URL = {API_URL}")
    print(f"IMAGE_PATH = {IMAGE_PATH.resolve()}")

    for level in CONCURRENCY_LEVELS:
        run_level(level)


if __name__ == "__main__":
    main()
