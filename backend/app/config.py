import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Google API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Environment Configuration
    ENV = os.getenv("ENV", "development")

    # Lighthouse Url
    LIGHTHOUSE_URL = "http://host.docker.internal:3001"

    SEO_AGENT_LANG = ""
    MAX_LOCATIONS_PER_ISSUE = ""
    LLM_MODEL = ""
    TIMEOUTS = ""
    SAFE_CSS_TOGGLE = ""
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required") 