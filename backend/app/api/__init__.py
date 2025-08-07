# API Controllers Package

from fastapi import APIRouter
from ..models import OptimizeRequest
from ..services import OptimizationService

router = APIRouter()

@router.post("/optimize")
def optimize(req: OptimizeRequest):
    """
    Controller: Handle optimize request and call service layer
    """
    modified_html = OptimizationService.optimize_html(req.html)
    return {"diff": modified_html} 