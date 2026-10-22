import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.schemas.payloads import AnnotateResponse, InferenceRequest, PredictResponse
from app.services.inference import YOLOInferenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["inference"])


def get_inference_service(request: Request) -> YOLOInferenceService:
    service = getattr(request.app.state, "inference_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference service is not initialised.",
        )
    return service


@router.post("/predict", response_model=PredictResponse)
async def predict(
    payload: InferenceRequest,
    service: YOLOInferenceService = Depends(get_inference_service),
) -> PredictResponse:
    try:
        return await service.predict_from_b64(payload.uuid, payload.image)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Prediction failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed.",
        ) from exc


@router.post("/annotate", response_model=AnnotateResponse)
async def annotate(
    payload: InferenceRequest,
    service: YOLOInferenceService = Depends(get_inference_service),
) -> AnnotateResponse:
    try:
        return await service.annotate_from_b64(payload.uuid, payload.image)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Annotation failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Annotation failed.",
        ) from exc
