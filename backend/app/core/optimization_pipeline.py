#!/usr/bin/env python3
"""
Full SEO Optimization Pipeline
Complete pipeline that runs Lighthouse analysis, LLM optimization, and HTML modification
"""

import time
import logging
from typing import Dict, Any, Optional
from app.services.seo_analysis_service import SEOAnalysisService
from app.core.lhr_parser import LHRTool
from app.core.matcher import match_issues
from app.core.issue_merger import transform_to_simple_issues_with_insertions
from app.core.llm_tool import LLMTool
from app.core.html_editor import HTMLEditor
from app.schemas.seo_analysis import SEOAnalysisResult, IssueInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizationPipeline:
    """
    Full SEO optimization pipeline that runs all steps and returns optimized HTML
    """
    
    def __init__(self, max_lighthouse_retries: int = 3, retry_delay: int = 2):
        """
        Initialize the optimization pipeline
        
        Args:
            max_lighthouse_retries: Maximum number of Lighthouse retry attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.max_lighthouse_retries = max_lighthouse_retries
        self.retry_delay = retry_delay
        
        # Initialize components
        self.seo_service = SEOAnalysisService()
        self.parser = LHRTool()
        self.llm_tool = LLMTool()
        self.html_editor = HTMLEditor()
    
    def run_lighthouse_analysis(self, html_content: str) -> tuple[Dict[str, Any], float]:
        """
        Run Lighthouse analysis with retry logic
        
        Args:
            html_content: HTML content to analyze
            
        Returns:
            Tuple of (lighthouse_result, seo_score)
            
        Raises:
            Exception: If all retry attempts fail
        """
        logger.info("🔍 Step 1: Running Lighthouse analysis...")
        
        for attempt in range(1, self.max_lighthouse_retries + 1):
            try:
                lighthouse_result = self.seo_service._call_lighthouse_service(html_content)
                seo_score = lighthouse_result.get('seoScore', 0)
                
                if seo_score > 0:
                    logger.info(f"✅ Lighthouse analysis successful! SEO score: {seo_score}")
                    return lighthouse_result, seo_score
                else:
                    logger.warning(f"⚠️ Lighthouse attempt {attempt} returned SEO score 0")
                    if attempt < self.max_lighthouse_retries:
                        time.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"❌ Lighthouse attempt {attempt} failed: {e}")
                if attempt == self.max_lighthouse_retries:
                    raise Exception(f"Lighthouse analysis failed after {self.max_lighthouse_retries} attempts: {str(e)}")
                time.sleep(self.retry_delay)
        
        raise Exception(f"Lighthouse analysis failed - all attempts returned SEO score 0")
    
    def parse_lighthouse_result(self, lighthouse_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Lighthouse result using LHR parser
        
        Args:
            lighthouse_result: Raw Lighthouse result
            
        Returns:
            Parsed result dictionary
        """
        logger.info("📊 Step 2: Parsing Lighthouse result...")
        parsed_result = self.parser.parse_lhr_json(lighthouse_result)
        logger.info(f"✅ Parser completed, found {len(parsed_result.get('issues', []))} issues")
        return parsed_result
    
    def match_issues_to_html(self, html_content: str, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match parsed issues to HTML content
        
        Args:
            html_content: Original HTML content
            parsed_result: Parsed Lighthouse result
            
        Returns:
            Matched result dictionary
        """
        logger.info("🎯 Step 3: Matching issues to HTML...")
        matched_result = match_issues(html_content, parsed_result)
        
        matched_issues = matched_result.get('issues', [])
        matched_count = len([i for i in matched_issues if i.get('match_status') == 'matched'])
        logger.info(f"✅ Matcher completed, total issues: {len(matched_issues)}, matched: {matched_count}")
        
        return matched_result
    
    def merge_issues(self, matched_result: Dict[str, Any]) -> list:
        """
        Merge and transform issues for optimization
        
        Args:
            matched_result: Matched issues result
            
        Returns:
            List of merged issues
        """
        logger.info("🔧 Step 4: Merging issues...")
        merged_issues = transform_to_simple_issues_with_insertions(matched_result)
        logger.info(f"✅ Issue merger completed, merged issues: {len(merged_issues)}")
        return merged_issues
    
    def build_final_result(self, parsed_result: Dict[str, Any], merged_issues: list, html_content: str) -> Any:
        """
        Build final result for LLM processing
        
        Args:
            parsed_result: Parsed Lighthouse result
            merged_issues: Merged issues list
            html_content: Original HTML content
            
        Returns:
            Final result object
        """
        logger.info("📝 Step 5: Building final result...")
        final_result = self.seo_service._build_final_result(
            parsed_result, 
            merged_issues, 
            html_content
        )
        logger.info("✅ Final result built successfully")
        return final_result
    
    def optimize_with_llm(self, final_result: Any) -> Dict[str, Any]:
        """
        Optimize issues using LLM
        
        Args:
            final_result: Final result object for LLM processing
            
        Returns:
            Optimized result dictionary
        """
        logger.info("🤖 Step 6: Running LLM optimization...")
        optimized_res = self.llm_tool.get_batch_modification(final_result)
        
        # Convert to dict if needed
        if hasattr(optimized_res, 'dict'):
            optimized_dict = optimized_res.dict()
        else:
            optimized_dict = optimized_res.__dict__
        
        logger.info(f"✅ LLM optimization completed, processed {len(optimized_dict.get('issues', []))} issues")
        return optimized_dict
    
    def apply_html_modifications(self, html_content: str, optimized_dict: Dict[str, Any]) -> str:
        """
        Apply HTML modifications including image captioning
        
        Args:
            html_content: Original HTML content
            optimized_dict: Optimized result dictionary
            
        Returns:
            Modified HTML string
        """
        logger.info("✏️ Step 7: Applying HTML modifications...")
        
        # Convert back to SEOAnalysisResult for the editor
        issues = []
        for issue_data in optimized_dict.get('issues', []):
            issue = IssueInfo(
                title=issue_data.get('title', ''),
                start_line=issue_data.get('start_line', 1),
                end_line=issue_data.get('end_line', 1),
                raw_html=issue_data.get('raw_html', ''),
                optimized_html=issue_data.get('optimized_html', '')
            )
            issues.append(issue)
        
        seo_result = SEOAnalysisResult(
            seo_score=optimized_dict.get('seo_score', 0.0),
            total_lines=optimized_dict.get('total_lines', len(html_content.split('\n'))),
            issues=issues,
            context=optimized_dict.get('context', '')
        )
        
        # Sort issues in descending order by end_line
        seo_result.issues.sort(key=lambda x: x.end_line, reverse=True)
        
        # Apply fixes using HTML editor (includes image captioning)
        optimized_html = self.html_editor.modify_html(html_content, seo_result)
        
        logger.info("✅ HTML modifications applied successfully")
        return optimized_html
    
    def run_full_pipeline(self, html_content: str) -> Dict[str, Any]:
        """
        Run the complete optimization pipeline
        
        Args:
            html_content: Original HTML content to optimize
            
        Returns:
            Dictionary containing optimization results
        """
        try:
            logger.info("🚀 Starting full SEO optimization pipeline...")
            
            # Step 1: Lighthouse analysis
            lighthouse_result, original_seo_score = self.run_lighthouse_analysis(html_content)
            
            # Step 2: Parse Lighthouse result
            parsed_result = self.parse_lighthouse_result(lighthouse_result)
            
            # Step 3: Match issues to HTML
            matched_result = self.match_issues_to_html(html_content, parsed_result)
            
            # Step 4: Merge issues
            merged_issues = self.merge_issues(matched_result)
            
            # Step 5: Build final result
            final_result = self.build_final_result(parsed_result, merged_issues, html_content)
            
            # Step 6: LLM optimization
            optimized_dict = self.optimize_with_llm(final_result)
            
            # Step 7: Apply HTML modifications
            optimized_html = self.apply_html_modifications(html_content, optimized_dict)
            
            logger.info("🎉 Full pipeline completed successfully!")
            
            # Return complete results
            return {
                "success": True,
                "modified_html": optimized_html,
                "optimization_result": optimized_dict,
                "original_seo_score": original_seo_score,
                "optimized_seo_score": optimized_dict.get('seo_score', 0.0),
                "issues_processed": len(optimized_dict.get('issues', [])),
                "pipeline_steps": [
                    "lighthouse_analysis",
                    "lhr_parsing", 
                    "issue_matching",
                    "issue_merging",
                    "llm_optimization",
                    "html_modification",
                    "image_captioning"
                ],
                "lighthouse_result": lighthouse_result,
                "parsed_result": parsed_result,
                "matched_result": matched_result,
                "merged_issues": merged_issues
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "step": "pipeline_execution"
            }


# Convenience function for quick usage
def optimize_html_full_pipeline(html_content: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Convenience function to run the full optimization pipeline
    
    Args:
        html_content: HTML content to optimize
        max_retries: Maximum Lighthouse retry attempts
        
    Returns:
        Optimization results dictionary
    """
    pipeline = OptimizationPipeline(max_lighthouse_retries=max_retries)
    return pipeline.run_full_pipeline(html_content)


# Example usage for testing
if __name__ == "__main__":
    # Test with sample HTML
    sample_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title></title>
</head>
<body>
    <h1>Sample Page</h1>
    <p>This page has SEO issues.</p>
    <img src="https://example.com/image.jpg" alt="">
</body>
</html>"""
    
    print("Testing OptimizationPipeline...")
    result = optimize_html_full_pipeline(sample_html)
    
    if result.get("success"):
        print(f"✅ Pipeline successful!")
        print(f"Original SEO Score: {result.get('original_seo_score')}")
        print(f"Optimized SEO Score: {result.get('optimized_seo_score')}")
        print(f"Issues Processed: {result.get('issues_processed')}")
    else:
        print(f"❌ Pipeline failed: {result.get('error')}")
