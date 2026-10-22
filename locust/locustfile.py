import base64
import binascii
import json
import os
import uuid
from pathlib import Path

from locust import FastHttpUser, constant, task

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE_PATH = PROJECT_ROOT / "samples" / "benchmark_640.jpg"
IMAGE_PATH = Path(os.getenv("LOCUST_IMAGE_PATH", str(DEFAULT_IMAGE_PATH)))
def _response_preview(response) -> str:
    text = getattr(response, "text", None)
    if text:
        return text[:200]

    content = getattr(response, "content", None)
    if content:
        try:
            return bytes(content[:200]).decode("utf-8", errors="replace")
        except Exception:
            return repr(content[:200])

    return ""


class WasteApiUser(FastHttpUser):
    wait_time = constant(0)

    def on_start(self) -> None:
        self.raw_bytes = IMAGE_PATH.read_bytes()

    def _payload(self) -> dict[str, str]:
        image_b64 = base64.b64encode(self.raw_bytes).decode("utf-8")
        return {
            "uuid": str(uuid.uuid4()),
            "image": image_b64,
        }

    @task(3)
    def predict(self) -> None:
        payload = self._payload()
        with self.client.post(
            "/api/predict",
            json=payload,
            name="POST /api/predict",
            catch_response=True,
            timeout=60,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"HTTP {response.status_code}: {_response_preview(response)}"
                )
                return

            try:
                data = json.loads(response.text)
            except json.JSONDecodeError:
                response.failure("Response is not valid JSON")
                return

            required_fields = {
                "uuid",
                "count",
                "detections",
                "boxes",
                "speed_preprocess_ms",
                "speed_inference_ms",
                "speed_postprocess_ms",
            }

            missing = required_fields.difference(data)
            if missing:
                response.failure(f"Missing fields: {sorted(missing)}")
                return

            if data["uuid"] != payload["uuid"]:
                response.failure("Response uuid does not match request uuid")
                return

            if data["count"] != len(data["detections"]) or data["count"] != len(data["boxes"]):
                response.failure("Count / detections / boxes mismatch")
                return

            response.success()

    @task(1)
    def annotate(self) -> None:
        payload = self._payload()
        with self.client.post(
            "/api/annotate",
            json=payload,
            name="POST /api/annotate",
            catch_response=True,
            timeout=60,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"HTTP {response.status_code}: {_response_preview(response)}"
                )
                return

            try:
                data = json.loads(response.text)
            except json.JSONDecodeError:
                response.failure("Response is not valid JSON")
                return

            if "uuid" not in data or "image" not in data:
                response.failure("Missing uuid or image in annotate response")
                return

            if data["uuid"] != payload["uuid"]:
                response.failure("Response uuid does not match request uuid")
                return

            try:
                base64.b64decode(data["image"], validate=True)
            except (binascii.Error, ValueError):
                response.failure("Annotated image is not valid base64")
                return

            response.success()
