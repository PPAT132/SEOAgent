# app/api/routes.py
from fastapi import APIRouter, Depends
from app.dependencies import get_validator_service

from app.services.validator_service import ValidatorService
router = APIRouter()

@router.get("/test")
def test_endpoint():
    return {"message": "Router is working"}

@router.post("/audit")
def audit_url(url: str, validator_service: ValidatorService = Depends(get_validator_service)):
    print("here")
    return validator_service.get_full_result(url)
