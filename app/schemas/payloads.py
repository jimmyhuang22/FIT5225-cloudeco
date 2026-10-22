from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    uuid: str = Field(..., min_length=1, description="Client correlation ID")
    image: str = Field(..., min_length=1, description="Base64-encoded image")


class DetectionBox(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., ge=0)
    height: int = Field(..., ge=0)
    probability: float = Field(..., ge=0.0, le=1.0)


class PredictResponse(BaseModel):
    uuid: str
    count: int = Field(..., ge=0)
    detections: list[str]
    boxes: list[DetectionBox]
    speed_preprocess_ms: float = Field(..., ge=0.0)
    speed_inference_ms: float = Field(..., ge=0.0)
    speed_postprocess_ms: float = Field(..., ge=0.0)


class AnnotateResponse(BaseModel):
    uuid: str
    image: str


class HealthResponse(BaseModel):
    status: str
