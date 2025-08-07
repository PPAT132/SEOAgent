# SEO Agent V1 - AI Agent Brain
from ..core.llm_tool import LLMTool

class OptimizationV1:
    """
    First version of SEO Agent - AI Agent brain that uses LLM tool
    """
    
    def __init__(self):
        print("DEBUG: Initializing OptimizationV1")
        self.llm_tool = LLMTool()
        print("DEBUG: LLMTool initialized successfully")
    
    def optimize_html(self, html: str) -> str:
        """
        Main method: Use LLM to optimize HTML for SEO
        """
        print(f"DEBUG: Starting HTML optimization for length: {len(html)}")
        
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
            
            print(f"DEBUG: Created prompt with length: {len(prompt)}")
            
            # Call LLM tool once and return the result
            print("DEBUG: Calling LLM tool...")
            optimized_html = self.llm_tool.generate_content(prompt)
            print(f"DEBUG: LLM returned result with length: {len(optimized_html)}")
            
            return optimized_html
            
        except Exception as e:
            print(f"DEBUG: SEO Agent V1 optimization failed: {str(e)}")
            # Return original HTML if optimization fails
            return html 