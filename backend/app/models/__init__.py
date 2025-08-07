from pydantic import BaseModel

class OptimizeRequest(BaseModel):
    html: str 