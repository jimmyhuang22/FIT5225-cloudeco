import base64
import json
import uuid
import os
from pathlib import Path
from urllib.request import Request, urlopen

from app.utils.image_codec import encode_file_to_base64

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/annotate")
IMAGE_PATH = Path("samples/benchmark_640.jpg")
OUTPUT_PATH = Path("samples/annotated_from_api.jpg")


def main() -> None:
    payload = {
        "uuid": str(uuid.uuid4()),
        "image": encode_file_to_base64(IMAGE_PATH),
    }

    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=60) as response:
        body = json.loads(response.read().decode("utf-8"))

    OUTPUT_PATH.write_bytes(base64.b64decode(body["image"], validate=True))

    print("uuid =", body["uuid"])
    print("saved =", OUTPUT_PATH.resolve())


if __name__ == "__main__":
    main()
