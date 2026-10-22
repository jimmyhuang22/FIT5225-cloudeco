import asyncio
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

try:
    import torch
except ImportError:
    torch = None

from app.core.config import (
    ANNOTATION_IMAGE_EXT,
    ANNOTATION_MAX_SIDE,
    JPEG_QUALITY,
    IMGSZ,
    CONF_THRESHOLD,
    MAX_DET,
)
from app.schemas.payloads import AnnotateResponse, DetectionBox, PredictResponse
from app.utils.image_codec import decode_base64_to_bgr, encode_bgr_to_base64

logger = logging.getLogger(__name__)


class YOLOInferenceService:
    def __init__(self, model_path: str | Path, max_workers: int = 1) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        self._configure_runtime()

        self._infer_executor = ThreadPoolExecutor(
            max_workers=max(1, int(max_workers)),
            thread_name_prefix="yolo-infer",
        )
        self._codec_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="yolo-codec",
        )

        self._model = YOLO(str(self.model_path))
        try:
            self._model.fuse()
        except Exception:
            pass

        self._class_names = self._normalise_class_names(self._model.names)
        self.ready = False

    @staticmethod
    def _configure_runtime() -> None:
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        os.environ.setdefault("MKL_NUM_THREADS", "1")
        os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

        try:
            cv2.setNumThreads(1)
        except Exception:
            pass

        if torch is not None:
            torch.set_num_threads(1)
            try:
                torch.set_num_interop_threads(1)
            except RuntimeError:
                pass

    @staticmethod
    def _normalise_class_names(names: object) -> dict[int, str]:
        if isinstance(names, dict):
            return {int(k): str(v) for k, v in names.items()}
        if isinstance(names, (list, tuple)):
            return {i: str(v) for i, v in enumerate(names)}
        return {}

    @property
    def class_names(self) -> dict[int, str]:
        return self._class_names

    async def _run_infer(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._infer_executor, partial(func, *args))

    async def _run_codec(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._codec_executor, partial(func, *args))

    def _predict_sync(self, image_bgr: np.ndarray):
        results = self._model.predict(
            source=image_bgr,
            device="cpu",
            imgsz=IMGSZ,
            conf=CONF_THRESHOLD,
            max_det=MAX_DET,
            verbose=False,
        )
        return results[0]

    async def warmup(self) -> None:
        dummy = np.zeros((IMGSZ, IMGSZ, 3), dtype=np.uint8)
        _ = await self._run_infer(self._predict_sync, dummy)
        self.ready = True
        logger.info("YOLO model warmup completed.")

    def _build_predict_response(self, request_id: str, result) -> PredictResponse:
        detections: list[str] = []
        boxes: list[DetectionBox] = []

        for box in result.boxes:
            cls_id = int(box.cls.item())
            confidence = float(box.conf.item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            x = max(0, int(round(x1)))
            y = max(0, int(round(y1)))
            width = max(0, int(round(x2 - x1)))
            height = max(0, int(round(y2 - y1)))

            detections.append(self._class_names.get(cls_id, str(cls_id)))
            boxes.append(
                DetectionBox(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    probability=confidence,
                )
            )

        speed = result.speed or {}

        return PredictResponse(
            uuid=request_id,
            count=len(detections),
            detections=detections,
            boxes=boxes,
            speed_preprocess_ms=float(speed.get("preprocess", 0.0)),
            speed_inference_ms=float(speed.get("inference", 0.0)),
            speed_postprocess_ms=float(speed.get("postprocess", 0.0)),
        )

    async def predict_from_b64(self, request_id: str, encoded: str) -> PredictResponse:
        started_at = time.perf_counter()

        t0 = time.perf_counter()
        image_bgr = await self._run_codec(decode_base64_to_bgr, encoded)
        decode_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        result = await self._run_infer(self._predict_sync, image_bgr)
        infer_ms = (time.perf_counter() - t1) * 1000.0

        t2 = time.perf_counter()
        response = await self._run_codec(self._build_predict_response, request_id, result)
        build_ms = (time.perf_counter() - t2) * 1000.0

        total_async_ms = (time.perf_counter() - started_at) * 1000.0

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "predict request_id=%s decode_ms=%.2f infer_ms=%.2f "
                "build_ms=%.2f total_async_ms=%.2f",
                request_id,
                decode_ms,
                infer_ms,
                build_ms,
                total_async_ms,
            )

        return response

    async def annotate_from_b64(self, request_id: str, encoded: str) -> AnnotateResponse:
        started_at = time.perf_counter()

        t0 = time.perf_counter()
        image_bgr = await self._run_codec(decode_base64_to_bgr, encoded)
        decode_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        result = await self._run_infer(self._predict_sync, image_bgr)
        infer_ms = (time.perf_counter() - t1) * 1000.0

        t2 = time.perf_counter()
        encoded_image = await self._run_codec(
            self._draw_resize_encode_sync,
            image_bgr,
            result,
        )
        draw_encode_ms = (time.perf_counter() - t2) * 1000.0

        total_async_ms = (time.perf_counter() - started_at) * 1000.0

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "annotate request_id=%s decode_ms=%.2f infer_ms=%.2f "
                "draw_encode_ms=%.2f total_async_ms=%.2f",
                request_id,
                decode_ms,
                infer_ms,
                draw_encode_ms,
                total_async_ms,
            )

        return AnnotateResponse(uuid=request_id, image=encoded_image)

    def close(self) -> None:
        self._infer_executor.shutdown(wait=True, cancel_futures=False)
        self._codec_executor.shutdown(wait=True, cancel_futures=False)

    def _draw_detections_inplace(self, image_bgr: np.ndarray, result) -> np.ndarray:
        output = image_bgr

        for box in result.boxes:
            cls_id = int(box.cls.item())
            confidence = float(box.conf.item())
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

            label_name = self._class_names.get(cls_id, str(cls_id))
            label = f"{label_name} {confidence:.2f}"

            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)

            (text_w, text_h), baseline = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                1,
            )
            text_y = max(text_h + 4, y1 - 6)

            cv2.rectangle(
                output,
                (x1, text_y - text_h - 4),
                (x1 + text_w + 4, text_y + baseline),
                (0, 255, 0),
                -1,
            )
            cv2.putText(
                output,
                label,
                (x1 + 2, text_y - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

        return output

    @staticmethod
    def _resize_for_annotation(image_bgr: np.ndarray) -> np.ndarray:
        if ANNOTATION_MAX_SIDE <= 0:
            return image_bgr

        height, width = image_bgr.shape[:2]
        longest_side = max(height, width)
        if longest_side <= ANNOTATION_MAX_SIDE:
            return image_bgr

        scale = ANNOTATION_MAX_SIDE / float(longest_side)
        resized_width = max(1, int(round(width * scale)))
        resized_height = max(1, int(round(height * scale)))

        return cv2.resize(
            image_bgr,
            (resized_width, resized_height),
            interpolation=cv2.INTER_AREA,
        )

    def _draw_resize_encode_sync(self, image_bgr: np.ndarray, result) -> str:
        annotated_image = self._draw_detections_inplace(image_bgr, result)
        resized_image = self._resize_for_annotation(annotated_image)
        return encode_bgr_to_base64(
            resized_image,
            extension=ANNOTATION_IMAGE_EXT,
            jpeg_quality=JPEG_QUALITY,
        )
