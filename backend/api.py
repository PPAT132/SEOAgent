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
    Optimize HTML for SEO improvements
    """
    # TODO: Implement actual SEO optimization logic
    dummy_diff = "\n".join(difflib.unified_diff([], [], lineterm=''))
    return {"diff": dummy_diff or "// TODO: diff will appear here"}
