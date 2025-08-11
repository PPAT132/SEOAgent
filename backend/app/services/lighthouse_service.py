import requests


class LighthouseService:
    def __init__(self, lighthouse_url):
        self.lighthouse_url = lighthouse_url

    def run_lighthouse_audit(self, target_url: str) -> dict:
        try:
            lighthouse_path = self.lighthouse_url + "/audit"
            print("path: " + lighthouse_path)
            response = requests.post(lighthouse_path, json={"url": target_url})
            response.raise_for_status()  # raises error for HTTP 4xx/5xx
            return response.json()
        except requests.RequestException as e:
            # Log or handle error appropriately
            return {"error": str(e)}
    
    def run_lighthouse_audit_html(self, html_content: str) -> dict:
        """
        Run Lighthouse audit on raw HTML content
        Creates temporary file and analyzes it with Lighthouse
        """
        try:
            lighthouse_path = self.lighthouse_url + "/audit-html"
            print("HTML audit path: " + lighthouse_path)
            response = requests.post(lighthouse_path, json={"html": html_content})
            response.raise_for_status()  # raises error for HTTP 4xx/5xx
            return response.json()
        except requests.RequestException as e:
            # Log or handle error appropriately
            return {"error": str(e)}