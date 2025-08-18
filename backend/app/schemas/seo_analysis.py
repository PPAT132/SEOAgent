#!/usr/bin/env python3
"""
SEO Analysis Result Schema
定义 SEO 分析结果的数据结构
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class IssueInfo(BaseModel):
    """单个问题的详细信息"""
    title: str = Field(..., description="问题标题/描述")
    start_line: int = Field(..., description="起始行号 (正数=替换, 负数=插入)")
    end_line: int = Field(..., description="结束行号 (正数=替换, 负数=插入)")
    raw_html: str = Field(..., description="原始HTML内容或建议的HTML")


class SEOAnalysisResult(BaseModel):
    """SEO 分析结果"""
    seo_score: float = Field(..., description="SEO 分数 (0-100)")
    total_lines: int = Field(..., description="HTML 文件总行数")
    issues: List[IssueInfo] = Field(..., description="问题列表，按结束行号从大到小排序")
    
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
