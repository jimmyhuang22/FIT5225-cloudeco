from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request, status

from app.api.routes import router as api_router
from app.core.config import APP_TITLE, APP_VERSION, INFERENCE_MAX_WORKERS, MODEL_PATH
from app.schemas.payloads import HealthResponse
from app.services.inference import YOLOInferenceService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = None
    try:
        service = YOLOInferenceService(
            model_path=MODEL_PATH,
            max_workers=INFERENCE_MAX_WORKERS,
        )
        await service.warmup()
        app.state.inference_service = service
        logger.info(
            "Inference service ready. Labels: %s",
            list(service.class_names.values()),
        )
        yield
    finally:
        if service is not None:
            service.close()


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root():
    return {"service": APP_TITLE, "docs": "/docs"}


@app.get("/healthz", response_model=HealthResponse, include_in_schema=False)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/readyz", response_model=HealthResponse, include_in_schema=False)
async def readyz(request: Request) -> HealthResponse:
    service = getattr(request.app.state, "inference_service", None)
    if service is None or not service.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not ready.",
        )
    return HealthResponse(status="ready")
