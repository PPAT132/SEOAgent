#!/usr/bin/env python3
"""
SEO Analysis Service
完整的 SEO 分析服务，整合 Lighthouse、解析器、匹配器和结果处理器
"""

import os
import sys
import requests
from typing import Optional, Dict, Any, List

# 添加 core 模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from app.core.lhr_parser import LHRTool
from app.core.matcher import match_issues
from app.core.issue_merger import transform_to_simple_issues_with_insertions
from app.schemas.seo_analysis import SEOAnalysisResult, IssueInfo


class SEOAnalysisService:
    """SEO 分析服务"""
    
    def __init__(self, lighthouse_url: str = None):
        """
        初始化 SEO 分析服务
        
        Args:
            lighthouse_url: Lighthouse 服务地址
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
        分析 HTML 内容，返回完整的 SEO 分析结果
        
        Args:
            html_content: 要分析的 HTML 内容
            
        Returns:
            SEOAnalysisResult: 完整的 SEO 分析结果
            
        Raises:
            Exception: 当任何步骤失败时抛出异常
        """
        try:
            print("🚀 开始 SEO 分析流程...")
            
            # 步骤1: 调用 Lighthouse 服务
            print("🔍 调用 Lighthouse 服务...")
            lighthouse_result = self._call_lighthouse_service(html_content)
            
            # 步骤2: 解析 Lighthouse 结果
            print("📊 解析 Lighthouse 结果...")
            parsed_result = self._run_parser(lighthouse_result)
            
            # 步骤3: 匹配问题到原始 HTML
            print("🎯 匹配问题到原始 HTML...")
            matched_result = self._run_matcher(html_content, parsed_result)
            
            # 步骤4: 处理匹配结果，合并重叠问题
            print("🔧 处理匹配结果...")
            processed_result = self._process_matched_result(matched_result)
            
            # 步骤5: 构建最终结果
            print("📝 构建最终结果...")
            final_result = self._build_final_result(parsed_result, processed_result, html_content)
            
            print("✅ SEO 分析完成!")
            return final_result
            
        except Exception as e:
            print(f"❌ SEO 分析失败: {e}")
            raise
    
    def _call_lighthouse_service(self, html_content: str) -> Dict[str, Any]:
        """调用 Lighthouse 服务"""
        try:
            response = requests.post(
                f"{self.lighthouse_url}/audit-html",
                json={"html": html_content},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Lighthouse 服务调用失败: {e}")
    
    def _run_parser(self, lighthouse_result: Dict[str, Any]) -> Dict[str, Any]:
        """运行 LHR 解析器"""
        try:
            parsed_result = self.parser.parse_lhr_json(lighthouse_result)
            return parsed_result
        except Exception as e:
            raise Exception(f"LHR 解析器运行失败: {e}")
    
    def _run_matcher(self, html_content: str, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """运行匹配器"""
        try:
            return match_issues(html_content, parsed_result)
        except Exception as e:
            raise Exception(f"匹配器运行失败: {e}")
    
    def _process_matched_result(self, matched_result: Dict[str, Any]) -> List[IssueInfo]:
        """处理匹配结果，合并重叠问题"""
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
            raise Exception(f"结果处理失败: {e}")
    
    def _build_final_result(self, parsed_result: Dict[str, Any], 
                           issues: List[IssueInfo], 
                           html_content: str) -> SEOAnalysisResult:
        """构建最终的 SEO 分析结果"""
        try:
            # 获取 SEO 分数
            seo_score = parsed_result.get("seo_score", 0.0)
            
            # 计算总行数
            total_lines = len(html_content.split('\n'))
            
            # 构建最终结果
            result = SEOAnalysisResult(
                seo_score=seo_score,
                total_lines=total_lines,
                issues=issues
            )
            
            return result
            
        except Exception as e:
            raise Exception(f"构建最终结果失败: {e}")
    
    def analyze_html_file(self, html_file_path: str) -> SEOAnalysisResult:
        """
        分析 HTML 文件，返回完整的 SEO 分析结果
        
        Args:
            html_file_path: HTML 文件路径
            
        Returns:
            SEOAnalysisResult: 完整的 SEO 分析结果
        """
        try:
            # 读取 HTML 文件
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 分析 HTML 内容
            return self.analyze_html(html_content)
            
        except FileNotFoundError:
            raise Exception(f"HTML 文件未找到: {html_file_path}")
        except Exception as e:
            raise Exception(f"读取 HTML 文件失败: {e}")


# 便捷函数
def analyze_html(html_content: str, lighthouse_url: str = None) -> SEOAnalysisResult:
    """
    便捷函数：分析 HTML 内容
    
    Args:
        html_content: HTML 内容
        lighthouse_url: Lighthouse 服务地址
        
    Returns:
        SEOAnalysisResult: SEO 分析结果
    """
    service = SEOAnalysisService(lighthouse_url)
    return service.analyze_html(html_content)


def analyze_html_file(html_file_path: str, lighthouse_url: str = None) -> SEOAnalysisResult:
    """
    便捷函数：分析 HTML 文件
    
    Args:
        html_file_path: HTML 文件路径
        lighthouse_url: Lighthouse 服务地址
        
    Returns:
        SEOAnalysisResult: SEO 分析结果
    """
    service = SEOAnalysisService(lighthouse_url)
    return service.analyze_html_file(html_file_path)
