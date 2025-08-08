from app.services.lighthouse_service import LighthouseService

class ValidatorService:
    def __init__(self, lighthouse_service: LighthouseService):
        self.lighthouse_service = lighthouse_service

    def get_full_result(self, target_url: str) -> dict:
        result = self.lighthouse_service.run_lighthouse_audit(target_url)
        return {"result": result}