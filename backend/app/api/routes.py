# app/api/routes.py
from fastapi import APIRouter, Depends
from app.dependencies import get_validator_service, get_optimization_service
from app.services.validator_service import ValidatorService
from app.services.optimization_v1 import OptimizationV1
from app.models import OptimizeRequest

router = APIRouter()

@router.get("/test")
def test_endpoint():
    return {"message": "Router is working"}

@router.post("/audit")
def audit_url(url: str, validator_service: ValidatorService = Depends(get_validator_service)):
    return validator_service.get_full_result(url)

@router.post("/optimizev1")
def optimize_html(req: OptimizeRequest, optimization_service: OptimizationV1 = Depends(get_optimization_service)):
    """
    Optimize HTML for SEO using the OptimizationV1 service.
    """
    optimized_html = optimization_service.optimize_html(req.html)
    return {"optimized_html": optimized_html}
