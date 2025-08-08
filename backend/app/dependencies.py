import os
from app.config import Config
from app.services.lighthouse_service import LighthouseService
from app.services.validator_service import ValidatorService

def get_lighthouse_service() -> LighthouseService:
    """
    Dependency provider for FastAPI to inject a configured lighthouse service.
    """
    return LighthouseService(lighthouse_url=Config.LIGHTHOUSE_URL)

def get_validator_service() -> ValidatorService:
    return ValidatorService(get_lighthouse_service())