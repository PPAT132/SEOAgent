from app.services.lighthouse_service import LighthouseService

class ValidatorService:
    def __init__(self, lighthouse_service: LighthouseService):
        self.lighthouse_service = lighthouse_service

    def get_full_result(self, target_url: str) -> dict:
        """
        Get full Lighthouse audit result for a live website URL
        """
        result = self.lighthouse_service.run_lighthouse_audit(target_url)
        return {"result": result}
    
    def get_html_audit_result(self, html_content: str) -> dict:
        """
        Get full Lighthouse audit result for raw HTML content
        Returns raw JSON for LLM processing
        """
        result = self.lighthouse_service.run_lighthouse_audit_html(html_content)
        return {"result": result}