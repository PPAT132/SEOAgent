from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bs4 import BeautifulSoup
import difflib

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OptimizeRequest(BaseModel):
    html: str

@app.post("/optimize")
def optimize(req: OptimizeRequest):
    """
    Echo back the HTML with 'modified ' prepended, for frontend-backend connectivity test
    """
    modified_html = "modified " + req.html
    return {"diff": modified_html}
