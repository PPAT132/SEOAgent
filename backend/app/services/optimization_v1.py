# SEO Agent V1 - AI Agent Brain
from ..core.llm_tool import LLMTool

class OptimizationV1:
    """
    First version of SEO Agent - AI Agent brain that uses LLM tool
    """
    
    def __init__(self):
        self.llm_tool = LLMTool()
    
    def optimize_html(self, html: str) -> str:
        """
        Main method: Use LLM to optimize HTML for SEO
        """
        try:
            # Create SEO optimization prompt
            prompt = f"""
            Please optimize the following HTML for better SEO. 
            Focus on:
            1. Improving meta tags
            2. Adding semantic HTML elements
            3. Optimizing heading structure
            4. Adding alt attributes to images
            5. Improving content structure
            
            HTML to optimize:
            {html}
            
            Return only the optimized HTML without any explanations.
            """
            
            # Call LLM tool once and return the result
            optimized_html = self.llm_tool.generate_content(prompt)
            
            return optimized_html
            
        except Exception as e:
            # Return original HTML if optimization fails
            return html 