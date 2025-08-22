# app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_validator_service, get_optimization_service
from app.services.validator_service import ValidatorService
from app.services.optimization_v1 import OptimizationV1
from app.models import OptimizeRequest
from app.core.image_captioner import ImageCaptioner
from app.core.optimization_pipeline import OptimizationPipeline
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Global instances (lazy loaded)
_captioner = None
_pipeline_v2 = None

def get_image_captioner():
    """Get or create the image captioner instance"""
    global _captioner
    if _captioner is None:
        _captioner = ImageCaptioner()
    return _captioner

# Global pipeline instance
_pipeline = None

def get_optimization_pipeline():
    """Get or create the optimization pipeline instance"""
    global _pipeline
    if _pipeline is None:
        _pipeline = OptimizationPipeline()
    return _pipeline

# Pydantic models for image captioning
class ImageCaptionRequest(BaseModel):
    image_url: str
    short: bool = True
    max_length: int = 50

class BatchImageCaptionRequest(BaseModel):
    image_urls: List[str]
    max_length: int = 50

class ImageCaptionResponse(BaseModel):
    image_url: str
    caption: Optional[str]
    success: bool
    error: Optional[str] = None

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
    seo_analysis_result = optimization_service.optimize_html(req.html)
    
    # Return the complete SEO analysis result
    return seo_analysis_result


@router.post("/optimize_v2")
def optimize_html_v2(req: OptimizeRequest):
    """
    Full SEO optimization pipeline (v2) - Returns modified HTML and optimization data
    
    This endpoint runs the complete pipeline:
    1. Lighthouse analysis
    2. LHR parsing
    3. Issue matching
    4. Issue merging
    5. LLM optimization
    6. HTML modification with image captioning
    
    Returns both the modified HTML and the optimization result JSON.
    """
    try:
        # Get the pipeline instance
        pipeline = get_optimization_pipeline()
        
        # Run the full pipeline
        result = pipeline.run_full_pipeline(req.html)
        
        # Return the result (success/error handling is done in the pipeline)
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "step": "endpoint_execution"
        }



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


@router.post("/caption-image", response_model=ImageCaptionResponse)
def caption_single_image(request: ImageCaptionRequest):
    """
    Generate a caption for a single image from URL
    """
    try:
        captioner = get_image_captioner()
        
        if request.short:
            caption = captioner.generate_short_caption(request.image_url)
        else:
            caption = captioner.generate_caption(request.image_url, max_length=request.max_length)
        
        return ImageCaptionResponse(
            image_url=request.image_url,
            caption=caption,
            success=caption is not None
        )
        
    except Exception as e:
        return ImageCaptionResponse(
            image_url=request.image_url,
            caption=None,
            success=False,
            error=str(e)
        )


@router.post("/caption-images", response_model=List[ImageCaptionResponse])
def caption_multiple_images(request: BatchImageCaptionRequest):
    """
    Generate captions for multiple images from URLs
    """
    try:
        captioner = get_image_captioner()
        results = captioner.batch_caption_images(request.image_urls, max_length=request.max_length)
        
        responses = []
        for url in request.image_urls:
            caption = results.get(url)
            responses.append(ImageCaptionResponse(
                image_url=url,
                caption=caption,
                success=caption is not None
            ))
        
        return responses
        
    except Exception as e:
        # Return error response for all images
        return [
            ImageCaptionResponse(
                image_url=url,
                caption=None,
                success=False,
                error=str(e)
            )
            for url in request.image_urls
        ]


@router.get("/caption-test")
def test_image_captioning():
    """
    Test endpoint for image captioning functionality
    """
    test_url = "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=300"
    
    try:
        captioner = get_image_captioner()
        caption = captioner.generate_short_caption(test_url)
        
        return {
            "success": True,
            "test_url": test_url,
            "caption": caption,
            "message": "Image captioning is working!"
        }
        
    except Exception as e:
        return {
            "success": False,
            "test_url": test_url,
            "error": str(e),
            "message": "Image captioning failed"
        }


@router.get("/optimize-v2-test")
def test_optimize_v2():
    """
    Test endpoint for optimize_v2 pipeline using sample HTML
    """
    # Sample HTML with SEO issues for testing
    test_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title></title>
</head>
<body>
    <h1>Sample Page with Images</h1>
    <p>Images have no alt attributes and valid URLs.</p>
    
    <img src="https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=400" alt="">
    <img src="https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400">
    
    <p>End of page.</p>
</body>
</html>"""
    
    try:
        from app.models import OptimizeRequest
        
        # Create request object
        req = OptimizeRequest(html=test_html)
        
        # Call optimize_v2
        result = optimize_html_v2(req)
        
        # Return a simplified response for testing
        if result.get("success"):
            return {
                "success": True,
                "message": "optimize_v2 pipeline test completed successfully!",
                "original_seo_score": result.get("original_seo_score"),
                "optimized_seo_score": result.get("optimized_seo_score"),
                "issues_processed": result.get("issues_processed"),
                "html_length_original": len(test_html),
                "html_length_optimized": len(result.get("modified_html", "")),
                "pipeline_steps": result.get("pipeline_steps"),
                "has_modified_html": bool(result.get("modified_html")),
                "has_optimization_result": bool(result.get("optimization_result"))
            }
        else:
            return {
                "success": False,
                "message": "optimize_v2 pipeline test failed",
                "error": result.get("error"),
                "step": result.get("step")
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": "optimize_v2 test endpoint failed",
            "error": str(e)
        }

