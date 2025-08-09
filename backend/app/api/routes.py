# app/api/routes.py
from fastapi import APIRouter, Depends
from app.dependencies import get_validator_service, get_optimization_service
from app.services.validator_service import ValidatorService
from app.services.optimization_v1 import OptimizationV1
from app.models import OptimizeRequest

router = APIRouter()

@router.get("/test")
def test_endpoint():
    return {"message": "Router is working"}

@router.post("/audit")
def audit_url(url: str, validator_service: ValidatorService = Depends(get_validator_service)):
    return validator_service.get_full_result(url)

@router.post("/optimizev1")
def optimize_html(req: OptimizeRequest, optimization_service: OptimizationV1 = Depends(get_optimization_service)):
    """
    Optimize HTML for SEO using the OptimizationV1 service.
    """
    optimized_html = optimization_service.optimize_html(req.html)
    # Return 'diff' field to match frontend expectation
    return {"diff": optimized_html}
@router.post("/lighthouse-raw")
def lighthouse_raw_json(req: OptimizeRequest, validator_service: ValidatorService = Depends(get_validator_service)):
    """
    🔧 Raw Lighthouse JSON endpoint - for LLM processing
    
    Input: Raw HTML content
    Output: Complete Lighthouse JSON report (no human formatting)
    """
    try:
        print(f"DEBUG: Received HTML content length: {len(req.html)}")
        print(f"DEBUG: HTML preview: {req.html[:200]}...")
        
        # Get raw Lighthouse result
        lighthouse_result = validator_service.get_html_audit_result(req.html)
        
        print(f"DEBUG: Lighthouse result: {lighthouse_result}")
        
        # Check if there's an error in the result
        if "result" in lighthouse_result and "error" in lighthouse_result["result"]:
            return {
                "success": False,
                "error": lighthouse_result["result"]["error"],
                "debug_info": "Lighthouse service connection failed"
            }
        
        # Return the complete JSON as-is for LLM processing
        return {
            "success": True,
            "lighthouse_data": lighthouse_result,
            "debug_info": "Analysis completed successfully"
        }
        
    except Exception as e:
        print(f"ERROR: Lighthouse analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "debug_info": "Python backend error"
        }

