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