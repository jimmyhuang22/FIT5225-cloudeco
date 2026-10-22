from pathlib import Path
import os

APP_TITLE = "CloudEco Waste Detection API"
APP_VERSION = "1.0.0"

MODEL_PATH = Path(os.getenv("MODEL_PATH", "models/best_model.pt"))
INFERENCE_MAX_WORKERS = max(1, int(os.getenv("INFERENCE_MAX_WORKERS", "1")))

ANNOTATION_IMAGE_EXT = os.getenv("ANNOTATION_IMAGE_EXT", ".jpg")
JPEG_QUALITY = max(50, min(100, int(os.getenv("JPEG_QUALITY", "50"))))
ANNOTATION_MAX_SIDE = max(0, int(os.getenv("ANNOTATION_MAX_SIDE", "320")))

IMGSZ = max(160, int(os.getenv("IMGSZ", "256")))
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.10"))
MAX_DET = max(1, int(os.getenv("MAX_DET", "20")))
