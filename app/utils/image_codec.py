import base64
import binascii
from pathlib import Path

import cv2
import numpy as np


def _strip_data_url_prefix(encoded: str) -> str:
    payload = encoded.strip()
    if payload.lower().startswith("data:image") and "," in payload:
        payload = payload.split(",", 1)[1]
    return "".join(payload.split())


def decode_base64_to_bgr(encoded: str) -> np.ndarray:
    if not encoded:
        raise ValueError("The image field is empty.")

    payload = _strip_data_url_prefix(encoded)

    try:
        raw_bytes = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("The image field is not valid base64.") from exc

    buffer = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Decoded bytes are not a valid image.")

    return image


def encode_bgr_to_base64(
    image: np.ndarray,
    extension: str = ".jpg",
    jpeg_quality: int = 90,
) -> str:
    if image is None or image.size == 0:
        raise ValueError("Cannot encode an empty image.")

    params: list[int] = []
    if extension.lower() in {".jpg", ".jpeg"}:
        params = [cv2.IMWRITE_JPEG_QUALITY, int(jpeg_quality)]

    success, buffer = cv2.imencode(extension, image, params)
    if not success:
        raise ValueError("OpenCV failed to encode the annotated image.")

    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def encode_file_to_base64(path: str | Path) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")
