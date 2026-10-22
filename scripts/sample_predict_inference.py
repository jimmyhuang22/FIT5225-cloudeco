import json
import os
import uuid
from pathlib import Path
from statistics import mean
from time import perf_counter
from urllib.request import Request, urlopen

from app.utils.image_codec import encode_file_to_base64

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/predict")
IMAGE_PATH = Path(os.getenv("IMAGE_PATH", "samples/benchmark_640.jpg"))
NUM_REQUESTS = max(1, int(os.getenv("NUM_REQUESTS", "10")))
TIMEOUT_SECONDS = max(1, int(os.getenv("TIMEOUT_SECONDS", "60")))


def main() -> None:
    image_b64 = encode_file_to_base64(IMAGE_PATH)
    inference_samples: list[float] = []
    client_samples: list[float] = []

    for index in range(1, NUM_REQUESTS + 1):
        payload = {
            "uuid": str(uuid.uuid4()),
            "image": image_b64,
        }

        request = Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        started_at = perf_counter()
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        client_ms = (perf_counter() - started_at) * 1000.0

        inference_ms = float(body["speed_inference_ms"])
        inference_samples.append(inference_ms)
        client_samples.append(client_ms)

        print(
            f"{index:02d}: speed_inference_ms={inference_ms:.2f}, "
            f"client_total_ms={client_ms:.2f}, count={body.get('count')}"
        )

    print(
        f"avg_speed_inference_ms={mean(inference_samples):.2f}, "
        f"min={min(inference_samples):.2f}, max={max(inference_samples):.2f}"
    )
    print(
        f"avg_client_total_ms={mean(client_samples):.2f}, "
        f"min={min(client_samples):.2f}, max={max(client_samples):.2f}"
    )


if __name__ == "__main__":
    main()
