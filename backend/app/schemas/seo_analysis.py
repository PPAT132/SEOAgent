#!/usr/bin/env python3
"""
SEO Analysis Result Schema
Defines the data structure for SEO analysis results
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class IssueInfo(BaseModel):
    """Detailed information for a single issue"""
    title: str = Field(..., description="Issue title/description")
    start_line: int = Field(..., description="Start line number (positive=replace, negative=insert)")
    end_line: int = Field(..., description="End line number (positive=replace, negative=insert)")
    raw_html: str = Field(..., description="Original HTML content or suggested HTML")

    optimized_html: str = Field("", description="the html that is returned by the llm")


class SEOAnalysisResult(BaseModel):
    """SEO analysis result"""
    seo_score: float = Field(..., description="SEO score (0-100)")
    total_lines: int = Field(..., description="Total number of lines in HTML file")
    issues: List[IssueInfo] = Field(..., description="List of issues, sorted by end line number from largest to smallest")
    context: str = Field(..., description="string of information about the html content")
    
    class Config:
        schema_extra = {
            "example": {
                "seo_score": 31.0,
                "total_lines": 705,
                "issues": [
                    {
                        "title": "Links are not crawlable",
                        "start_line": 10,
                        "end_line": 20,
                        "raw_html": "<a href=\"javascript:void(0)\">click here</a>"
                    },
                    {
                        "title": "Document does not have a meta description",
                        "start_line": -5,
                        "end_line": -5,
                        "raw_html": "<meta name=\"description\" content=\"Your page description here\">"
                    },
                    {
                        "title": "Image elements do not have [alt] attributes",
                        "start_line": 25,
                        "end_line": 30,
                        "raw_html": "<img src=\"photo.jpg\" class=\"photo\">"
                    }
                ]
            }
        }
