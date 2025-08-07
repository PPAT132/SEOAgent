# Services Package

from ..core import modify_html

class OptimizationService:
    @staticmethod
    def optimize_html(html: str) -> str:
        """
        Service layer: Call core logic to modify HTML
        """
        return modify_html(html) 