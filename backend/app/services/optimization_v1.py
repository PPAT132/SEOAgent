# SEO Agent V1 - AI Agent Brain
from ..core.llm_tool import LLMTool
from ..services.seo_analysis_service import SEOAnalysisService

class OptimizationV1:
    """
    First version of SEO Agent - AI Agent brain that uses LLM tool
    """
    
    def __init__(self):
        self.ask_lighthouse = SEOAnalysisService()
    
    def optimize_html(self, html: str) -> dict:
        """
        Main method: Use LLM to optimize HTML for SEO
        """
        try:
            # Call SEO analysis service
            analysis_result = self.ask_lighthouse.analyze_html(html)
            
            # Return the raw analysis result as a dictionary
            if hasattr(analysis_result, 'dict'):
                # If it's a Pydantic model, convert to dict
                return analysis_result.dict()
            elif hasattr(analysis_result, '__dict__'):
                # If it's a regular object, get its dict
                return analysis_result.__dict__
            else:
                # If it's already a dict or other type
                return analysis_result
            
        except Exception as e:
            return {"error": f"Error during optimization: {str(e)}"}
    
    def _format_analysis_report(self, result_dict: dict, original_html: str) -> str:
        """Format the analysis result into a readable report"""
        try:
            report_lines = []
            report_lines.append("=" * 50)
            report_lines.append("SEO ANALYSIS REPORT")
            report_lines.append("=" * 50)
            
            # Add basic info
            if 'seo_score' in result_dict:
                report_lines.append(f"SEO Score: {result_dict['seo_score']}")
            
            # Add issues
            if 'issues' in result_dict and result_dict['issues']:
                report_lines.append(f"\nFound {len(result_dict['issues'])} issues:")
                for i, issue in enumerate(result_dict['issues'], 1):
                    if isinstance(issue, dict):
                        report_lines.append(f"\n{i}. {issue.get('title', 'Unknown issue')}")
                        if 'ranges' in issue:
                            report_lines.append(f"   Ranges: {issue.get('ranges', 'N/A')}")
                        if 'raw_html' in issue:
                            report_lines.append(f"   HTML: {issue.get('raw_html', 'N/A')[:100]}...")
                    else:
                        report_lines.append(f"\n{i}. {str(issue)}")
            else:
                report_lines.append("\nNo issues found!")
            
            # Add raw data for debugging
            report_lines.append(f"\n" + "=" * 50)
            report_lines.append("RAW ANALYSIS DATA")
            report_lines.append("=" * 50)
            import json
            report_lines.append(json.dumps(result_dict, indent=2, default=str))
            
            return "\n".join(report_lines)
            
        except Exception as e:
            return f"Analysis completed but formatting failed: {str(e)}\nRaw result: {str(result_dict)}" 