#!/usr/bin/env python3
"""
Test SEO Analysis Service
Validate the full SEO analysis flow
"""

import os
import sys
import json
from datetime import datetime

# Add app module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.seo_analysis_service import SEOAnalysisService, analyze_html_file


def test_seo_service():
    """Test SEO analysis service"""
    print("🧪 Start testing SEO Analysis Service")
    print("="*60)
    
    # Resolve test HTML file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_file_path = os.path.join(script_dir, "test_seo_page.html")
    
    if not os.path.exists(html_file_path):
        print(f"❌ Test HTML file not found: {html_file_path}")
        return False
    
    try:
        # Create service instance
        service = SEOAnalysisService()
        
        # Analyze HTML file
        print(f"📄 Analyze HTML file: {html_file_path}")
        result = service.analyze_html_file(html_file_path)
        
        # Show result summary
        print(f"\n📊 Result summary:")
        print(f"SEO Score: {result.seo_score}")
        print(f"Total lines: {result.total_lines}")
        print(f"Issue count: {len(result.issues)}")
        
        # Show each issue
        for i, issue in enumerate(result.issues, 1):
            print(f"\n{i}. Issue: {issue.title}")
            print(f"   Lines: {issue.start_line}-{issue.end_line}")
            print(f"   HTML: {issue.raw_html}")
        
        # Save result to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"seo_service_result_{timestamp}.json"
        
        # Convert to dict and save
        result_dict = result.dict()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Test completed!")
        print(f"Result saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_convenience_functions():
    """Test convenience helpers"""
    print("\n🧪 Test convenience functions")
    print("="*60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_file_path = os.path.join(script_dir, "test_seo_page.html")
    
    try:
        # Test helper
        result = analyze_html_file(html_file_path)
        print(f"✅ Convenience function OK!")
        print(f"SEO Score: {result.seo_score}")
        print(f"Issue count: {len(result.issues)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Convenience function failed: {e}")
        return False


def main():
    """Entrypoint"""
    print("🚀 SEO Analysis Service tests")
    print("="*60)
    
    # Test main service
    service_ok = test_seo_service()
    
    # Test convenience helpers
    convenience_ok = test_convenience_functions()
    
    if service_ok and convenience_ok:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")
    
    print("\nTroubleshooting:")
    print("1) Ensure Lighthouse service is running: cd ../lighthouse-service && node server.js")
    print("2) Check port 3002 is available")
    print("3) Verify the test HTML file exists and is readable")


if __name__ == "__main__":
    main()
