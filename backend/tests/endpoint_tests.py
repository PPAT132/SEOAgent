import requests

def test_audit_endpoint():
    # The URL of your FastAPI endpoint
    api_url = "http://127.0.0.1:8000/audit"
    
    # The URL you want to audit
    target_url = "https://myanimelist.net/"
    
    try:
        # Make a POST request to the audit endpoint
        response = requests.post(
            api_url,
            params={"url": target_url}  # Since your endpoint expects url as a query parameter
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Print the response
        result = response.json()
        print(f"Audit Result: {result}")
        print(f"SEO Score: {result.get('seo_score', 'N/A')}")
        
    except requests.RequestException as e:
        print(f"Error calling audit endpoint: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_audit_endpoint()