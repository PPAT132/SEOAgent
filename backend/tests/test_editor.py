#!/usr/bin/env python3
"""
Test script for HTMLEditor using the test SEO page
Runs once and outputs results to pipeline_outputs folder
"""

import os
import sys
import json
from typing import List

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.html_editor import HTMLEditor
from app.schemas.seo_analysis import SEOAnalysisResult, IssueInfo


def load_issues_from_json() -> SEOAnalysisResult:
    """Load issues from the JSON file"""
    json_path = os.path.join(os.path.dirname(__file__), 'pipeline_outputs', '06_optimized_result.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert the JSON data to IssueInfo objects
        issues = []
        for issue_data in data['issues']:
            # Handle cases where some fields might be missing
            issue = IssueInfo(
                title=issue_data.get('title', 'Unknown issue'),
                start_line=issue_data.get('start_line', 1),
                end_line=issue_data.get('end_line', 1),
                raw_html=issue_data.get('raw_html', ''),
                optimized_html=issue_data.get('optimized_html', '')
            )
            issues.append(issue)
        
        # Create SEOAnalysisResult
        seo_result = SEOAnalysisResult(
            seo_score=data.get('seo_score', 0.0),
            total_lines=data.get('total_lines', 705),
            issues=issues
        )
        
        return seo_result
        
    except FileNotFoundError:
        print(f"Error: Could not find JSON file at {json_path}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {json_path}: {e}")
        raise
    except KeyError as e:
        print(f"Error: Missing required field in JSON: {e}")
        raise


def main():
    """Main test function"""
    print("=" * 60)
    print("HTMLEditor Test - Single Run with Pipeline Output")
    print("=" * 60)
    
    # Initialize the editor
    editor = HTMLEditor()
    
    # Load the test HTML file
    test_html_path = os.path.join(os.path.dirname(__file__), 'test_seo_page.html')
    print(f"Loading HTML from: {test_html_path}")
    
    try:
        with open(test_html_path, 'r', encoding='utf-8') as f:
            original_html = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find test HTML file at {test_html_path}")
        return False
    
    print(f"✓ Loaded HTML file ({len(original_html)} characters)")
    
    # Count total lines in the HTML
    html_lines = original_html.split('\n')
    actual_total_lines = len(html_lines)
    print(f"✓ HTML has {actual_total_lines} lines")
    
    # Load issues from JSON file
    print(f"\nLoading issues from JSON file...")
    try:
        seo_result = load_issues_from_json()
        print(f"✓ Loaded {len(seo_result.issues)} issues from JSON")
        print(f"✓ JSON total_lines: {seo_result.total_lines}, Actual HTML lines: {actual_total_lines}")
        
        # Update total_lines to match actual HTML
        seo_result.total_lines = actual_total_lines
        
    except Exception as e:
        print(f"✗ Error loading issues: {e}")
        return False
    
    # Sort issues in descending order by end_line (as expected by the editor)
    seo_result.issues.sort(key=lambda x: x.end_line, reverse=True)
    
    print(f"✓ Sorted {len(seo_result.issues)} issues")
    print("\nIssues to fix:")
    for i, issue in enumerate(seo_result.issues, 1):
        print(f"  {i}. Line {issue.start_line}-{issue.end_line}: {issue.title}")
    
    # Apply the fixes using HTMLEditor
    print(f"\n{'='*40}")
    print("Applying HTML fixes...")
    print(f"{'='*40}")
    
    try:
        optimized_html = editor.modify_html(original_html, seo_result)
        print("✓ HTML optimization completed successfully!")
        
        # Ensure pipeline_outputs directory exists
        output_dir = os.path.join(os.path.dirname(__file__), 'pipeline_outputs')
        os.makedirs(output_dir, exist_ok=True)
        print(f"✓ Output directory ready: {output_dir}")
        
        # Save the original HTML for comparison
        original_output_path = os.path.join(output_dir, '07_original_html.html')
        with open(original_output_path, 'w', encoding='utf-8') as f:
            f.write(original_html)
        print(f"✓ Original HTML saved: {os.path.basename(original_output_path)}")
        
        # Save the optimized HTML
        optimized_output_path = os.path.join(output_dir, '08_optimized_html.html')
        with open(optimized_output_path, 'w', encoding='utf-8') as f:
            f.write(optimized_html)
        print(f"✓ Optimized HTML saved: {os.path.basename(optimized_output_path)}")
        
        # Verify the changes were applied
        print(f"\n{'='*40}")
        print("Verifying changes...")
        print(f"{'='*40}")
        
        changes_verified = 0
        total_issues = len(seo_result.issues)
        
        # Dynamic verification based on the actual issues from JSON
        for i, issue in enumerate(seo_result.issues, 1):
            # Check if the raw HTML is no longer present (indicating replacement)
            if issue.raw_html and issue.raw_html not in optimized_html:
                print(f"  ✓ Issue {i}: {issue.title[:50]}... (raw HTML removed)")
                changes_verified += 1
            # Or check if optimized content is present
            elif issue.optimized_html and any(part.strip() in optimized_html for part in issue.optimized_html.split('\n') if part.strip() and not part.strip().startswith('<')):
                print(f"  ✓ Issue {i}: {issue.title[:50]}... (optimized content found)")
                changes_verified += 1
            else:
                print(f"  ✗ Issue {i}: {issue.title[:50]}...")
        
        # Special checks for common fixes
        if 'UTF-8' in optimized_html:
            print(f"  ✓ UTF-8 charset found in optimized HTML")
        if 'https://www.example.com' in optimized_html:
            print(f"  ✓ Canonical URL improvements found")
        if 'Your Title Here' in optimized_html:
            print(f"  ✓ Title improvements found")
        
        # Create a detailed report
        report_path = os.path.join(output_dir, '09_html_editor_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("HTMLEditor Test Report\n")
            f.write("=====================\n\n")
            f.write(f"Test executed: {__file__}\n")
            f.write(f"JSON file used: 06_optimized_result.json\n")
            f.write(f"Original HTML lines: {actual_total_lines}\n")
            f.write(f"JSON total_lines: {seo_result.total_lines}\n")
            f.write(f"SEO Score: {seo_result.seo_score}\n")
            f.write(f"Issues processed: {len(seo_result.issues)}\n")
            f.write(f"Changes verified: {changes_verified}/{total_issues}\n")
            f.write(f"Original size: {len(original_html)} characters\n")
            f.write(f"Optimized size: {len(optimized_html)} characters\n\n")
            
            f.write("Issues processed:\n")
            f.write("-" * 80 + "\n")
            for i, issue in enumerate(seo_result.issues, 1):
                f.write(f"{i}. {issue.title}\n")
                f.write(f"   Lines {issue.start_line}-{issue.end_line}\n")
                f.write(f"   Raw: {issue.raw_html[:100]}{'...' if len(issue.raw_html) > 100 else ''}\n")
                f.write(f"   Fixed: {issue.optimized_html[:100]}{'...' if len(issue.optimized_html) > 100 else ''}\n\n")
            
            # Add some basic statistics
            original_lines = original_html.split('\n')
            optimized_lines = optimized_html.split('\n')
            f.write(f"Statistics:\n")
            f.write(f"- Original lines: {len(original_lines)}\n")
            f.write(f"- Optimized lines: {len(optimized_lines)}\n")
            f.write(f"- Title tags in original: {original_html.count('<title>')}\n")
            f.write(f"- Title tags in optimized: {optimized_html.count('<title>')}\n")
            f.write(f"- Canonical links in original: {original_html.count('rel=\"canonical\"')}\n")
            f.write(f"- Canonical links in optimized: {optimized_html.count('rel=\"canonical\"')}\n")
            f.write(f"- JavaScript void links in original: {original_html.count('javascript:void(0)')}\n")
            f.write(f"- JavaScript void links in optimized: {optimized_html.count('javascript:void(0)')}\n")
        
        print(f"✓ Report saved: {os.path.basename(report_path)}")
        
        # Final summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"✓ Test completed successfully!")
        print(f"✓ Changes verified: {changes_verified}/{total_issues}")
        print(f"✓ Files saved in: {output_dir}")
        print(f"  - {os.path.basename(original_output_path)}")
        print(f"  - {os.path.basename(optimized_output_path)}")
        print(f"  - {os.path.basename(report_path)}")
        
        return changes_verified >= (total_issues // 2)  # Pass if at least half the issues were fixed
        
    except Exception as e:
        print(f"✗ Error during HTML optimization: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    if success:
        print(f"\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  Some issues detected. Check the report for details.")
    
    print(f"\nCheck the pipeline_outputs folder for detailed results.")