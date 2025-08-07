# API Controllers Package

from fastapi import APIRouter
from ..models import OptimizeRequest
from ..services.optimization_v1 import OptimizationV1

router = APIRouter()

@router.post("/optimizev1")
def optimizev1(req: OptimizeRequest):
    """
    Controller: Handle optimize request and call OptimizationV1 directly
    """
    print(f"DEBUG: Received request with HTML length: {len(req.html)}")
    print(f"DEBUG: HTML preview: {req.html[:200]}...")
    
    try:
        optimization_agent = OptimizationV1()
        print("DEBUG: OptimizationV1 agent created successfully")
        
        optimized_html = optimization_agent.optimize_html(req.html)
        print(f"DEBUG: Optimization completed. Result length: {len(optimized_html)}")
        print(f"DEBUG: Result preview: {optimized_html[:200]}...")
        
        return {"diff": optimized_html}
    except Exception as e:
        print(f"DEBUG: Error in optimizev1 endpoint: {str(e)}")
        return {"diff": f"Error: {str(e)}"} 