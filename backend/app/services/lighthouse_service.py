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
    
    def get_required_lighthouse_data(self, content: str, is_url: bool) -> dict:
        # 1) invoke the right audit endpoint
        response = (
            self.run_lighthouse_audit(content)
            if is_url
            else self.run_lighthouse_audit_html(content)
        )

        # 2) if an error key is present or success is false, bubble it up
        if response.get("error") or response.get("success") is False:
            return {"error": response.get("error", "Lighthouse audit failed")}

        seo_score = response.get("seoScore", 0)
        audits    = response.get("audits", {})
        print("lol: ", response.keys())

        return {
            "seo_score": seo_score,
            "audits":    audits
        }