import requests

Lighthouse_URL = "http://localhost:3001/audit"

def run_lighthouse_audit(target_url: str) -> dict:
    try:
        response = requests.post(LIGHTHOUSE_URL, json={"url": target_url})
        response.raise_for_status()  # raises error for HTTP 4xx/5xx
        return response.json()
    except requests.RequestException as e:
        # Log or handle error appropriately
        return {"error": str(e)}