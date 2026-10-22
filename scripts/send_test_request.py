import json
import uuid
import os
from pathlib import Path
from urllib.request import Request, urlopen

from app.utils.image_codec import encode_file_to_base64

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/predict")
IMAGE_PATH = Path("samples/benchmark_640.jpg")


def main() -> None:
    payload = {
        "uuid": str(uuid.uuid4()),
        "image": encode_file_to_base64(IMAGE_PATH),
    }

    data = json.dumps(payload).encode("utf-8")
    request = Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request) as response:
        print(response.read().decode("utf-8"))


if __name__ == "__main__":
    main()
