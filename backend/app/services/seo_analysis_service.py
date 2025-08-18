#!/usr/bin/env python3
"""
SEO Analysis Service
End-to-end SEO analysis service integrating Lighthouse, parser, matcher and merger.
"""

import os
import sys
import requests
from typing import Optional, Dict, Any, List

# Add core module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from app.core.lhr_parser import LHRTool
from app.core.matcher import match_issues
from app.core.issue_merger import transform_to_simple_issues_with_insertions
from app.schemas.seo_analysis import SEOAnalysisResult, IssueInfo


class SEOAnalysisService:
    """SEO analysis service"""
    
    def __init__(self, lighthouse_url: str = None):
        """
        Initialize SEO analysis service.
        
        Args:
            lighthouse_url: Lighthouse service base URL
        """
        # Use config if no URL provided
        if lighthouse_url is None:
            from ..config import Config
            self.lighthouse_url = Config.LIGHTHOUSE_URL
        else:
            self.lighthouse_url = lighthouse_url
        self.parser = LHRTool()
        
    def analyze_html(self, html_content: str) -> SEOAnalysisResult:
        """
        Analyze raw HTML and return a complete SEO analysis result.
        
        Args:
            html_content: HTML content to analyze
            
        Returns:
            SEOAnalysisResult: Complete SEO analysis result
            
        Raises:
            Exception: When any step fails
        """
        try:
            print("🚀 Starting SEO analysis...")
            
            # Step 1: call Lighthouse service
            print("🔍 Calling Lighthouse service...")
            lighthouse_result = self._call_lighthouse_service(html_content)
            
            # Step 2: parse Lighthouse result
            print("📊 Parsing Lighthouse result...")
            parsed_result = self._run_parser(lighthouse_result)
            
            # Step 3: match issues to original HTML
            print("🎯 Matching issues to HTML...")
            matched_result = self._run_matcher(html_content, parsed_result)
            
            # Step 4: process matched result and merge overlaps
            print("🔧 Processing matched result...")
            processed_result = self._process_matched_result(matched_result)
            
            # Step 5: build final result
            print("📝 Building final result...")
            final_result = self._build_final_result(parsed_result, processed_result, html_content)
            
            print("✅ SEO analysis complete!")
            return final_result
            
        except Exception as e:
            print(f"❌ SEO analysis failed: {e}")
            raise
    
    def _call_lighthouse_service(self, html_content: str) -> Dict[str, Any]:
        """Call Lighthouse microservice"""
        try:
            response = requests.post(
                f"{self.lighthouse_url}/audit-html",
                json={"html": html_content},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Lighthouse service call failed: {e}")
    
    def _run_parser(self, lighthouse_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run LHR parser"""
        try:
            parsed_result = self.parser.parse_lhr_json(lighthouse_result)
            return parsed_result
        except Exception as e:
            raise Exception(f"LHR parser failed: {e}")
    
    def _run_matcher(self, html_content: str, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run matcher"""
        try:
            return match_issues(html_content, parsed_result)
        except Exception as e:
            raise Exception(f"Matcher failed: {e}")
    
    def _process_matched_result(self, matched_result: Dict[str, Any]) -> List[IssueInfo]:
        """Process matched result and merge overlapping issues"""
        try:
            # 使用 issue_merger 处理数据，支持插入操作
            processed_data = transform_to_simple_issues_with_insertions(matched_result)
            
            # 转换为 IssueInfo 对象
            issues = []
            for issue_data in processed_data:
                issue = IssueInfo(
                    title=issue_data['title'],
                    start_line=issue_data['start_line'],
                    end_line=issue_data['end_line'],
                    raw_html=issue_data['raw_html']
                )
                issues.append(issue)
            
            return issues
            
        except Exception as e:
            raise Exception(f"Result processing failed: {e}")
    
    def _build_final_result(self, parsed_result: Dict[str, Any], 
                           issues: List[IssueInfo], 
                           html_content: str) -> SEOAnalysisResult:
        """Build final SEO analysis result"""
        try:
            # Get SEO score
            seo_score = parsed_result.get("seo_score", 0.0)
            
            # Compute total line count
            total_lines = len(html_content.split('\n'))
            
            # Build final Pydantic model
            result = SEOAnalysisResult(
                seo_score=seo_score,
                total_lines=total_lines,
                issues=issues
            )
            
            return result
            
        except Exception as e:
            raise Exception(f"Build final result failed: {e}")
    
    def analyze_html_file(self, html_file_path: str) -> SEOAnalysisResult:
        """
        Analyze an HTML file and return the complete SEO analysis result.
        
        Args:
            html_file_path: Path to the HTML file
            
        Returns:
            SEOAnalysisResult: Complete SEO analysis result
        """
        try:
            # 读取 HTML 文件
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 分析 HTML 内容
            return self.analyze_html(html_content)
            
        except FileNotFoundError:
            raise Exception(f"HTML file not found: {html_file_path}")
        except Exception as e:
            raise Exception(f"Failed to read HTML file: {e}")


# Convenience helpers
def analyze_html(html_content: str, lighthouse_url: str = None) -> SEOAnalysisResult:
    """
    Convenience function: analyze raw HTML
    
    Args:
        html_content: HTML content
        lighthouse_url: Lighthouse service base URL
        
    Returns:
        SEOAnalysisResult: SEO analysis result
    """
    service = SEOAnalysisService(lighthouse_url)
    return service.analyze_html(html_content)


def analyze_html_file(html_file_path: str, lighthouse_url: str = None) -> SEOAnalysisResult:
    """
    Convenience function: analyze an HTML file
    
    Args:
        html_file_path: Path to the HTML file
        lighthouse_url: Lighthouse service base URL
        
    Returns:
        SEOAnalysisResult: SEO analysis result
    """
    service = SEOAnalysisService(lighthouse_url)
    return service.analyze_html_file(html_file_path)
