#!/usr/bin/env python3
"""
Result Processor - process matched results, group by line ranges and sort.
Designed to prepare inputs for LLM batch processing of multiple issues.
"""

from typing import Any, Dict, List, Tuple
import re


def extract_line_ranges(issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group issues by their line ranges.
    Returns: {"start_line-end_line": [issues]}
    """
    line_ranges = {}
    
    for issue in issues:
        if issue.get("match_status") != "matched":
            continue
            
        start_line = issue.get("match_line_start")
        end_line = issue.get("match_line_end")
        
        if start_line is None or end_line is None:
            continue
            
        # Create line range key
        range_key = f"{start_line}-{end_line}"
        
        if range_key not in line_ranges:
            line_ranges[range_key] = []
        line_ranges[range_key].append(issue)
    
    return line_ranges


def merge_overlapping_ranges(line_ranges: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Merge overlapping or adjacent line ranges
    For example: 10-20 and 13-14 merge to 10-20
    """
    if not line_ranges:
        return {}
    
    # Parse ranges and sort
    ranges = []
    for range_key, issues in line_ranges.items():
        start, end = map(int, range_key.split('-'))
        ranges.append((start, end, range_key, issues))
    
    # Sort by start line
    ranges.sort(key=lambda x: x[0])
    
    # Merge overlapping or adjacent ranges
    merged = []
    current_start, current_end, current_key, current_issues = ranges[0]
    
    for start, end, key, issues in ranges[1:]:
        # If current range overlaps or is adjacent to next range
        if start <= current_end + 1:
            # Extend current range
            current_end = max(current_end, end)
            current_issues.extend(issues)
        else:
            # Save current and start a new range
            merged.append((current_start, current_end, current_issues))
            current_start, current_end, current_issues = start, end, issues
    
    # Append the last accumulated range
    merged.append((current_start, current_end, current_issues))
    
    # Rebuild dictionary form
    result = {}
    for start, end, issues in merged:
        range_key = f"{start}-{end}"
        result[range_key] = issues
    
    return result


def sort_ranges_by_size(line_ranges: Dict[str, List[Dict[str, Any]]]) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """
    Sort ranges by size (largest to smallest) and return an ordered list.
    """
    if not line_ranges:
        return []
    
    # Compute line counts and sort by end line desc for diff application
    sorted_ranges = []
    for range_key, issues in line_ranges.items():
        start, end = map(int, range_key.split('-'))
        line_count = end - start + 1
        sorted_ranges.append((line_count, range_key, issues))
    
    # Sort by end line desc (apply from bottom to top)
    sorted_ranges.sort(key=lambda x: int(x[1].split('-')[1]), reverse=True)
    
    # Return ordered list
    return [(range_key, issues) for _, range_key, issues in sorted_ranges]


def add_raw_html_context(line_ranges: Dict[str, List[Dict[str, Any]]], html_content: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Add raw HTML section for each line range.
    """
    if not html_content:
        return line_ranges
    
    html_lines = html_content.split('\n')
    
    for range_key, issues in line_ranges.items():
        start, end = map(int, range_key.split('-'))
        
        # Extract HTML for the line range (convert 1-based to 0-based)
        start_idx = max(0, start - 1)
        end_idx = min(len(html_lines), end)
        
        range_html = '\n'.join(html_lines[start_idx:end_idx])
        
        # Attach range HTML to each issue
        for issue in issues:
            issue['raw_html'] = range_html
            issue['line_range'] = range_key
    
    return line_ranges


def process_matched_results(matched_result: Dict[str, Any], html_content: str = None) -> Dict[str, Any]:
    """
    Process the matched result into grouped-by-line-range data.
    """
    issues = matched_result.get("issues", [])
    
    # 1) Group by line ranges
    line_ranges = extract_line_ranges(issues)
    
    # 2) Merge overlapping ranges
    merged_ranges = merge_overlapping_ranges(line_ranges)
    
    # 3) Sort by size (largest to smallest)
    sorted_ranges = sort_ranges_by_size(merged_ranges)
    
    # 4) Add HTML context
    final_ranges = add_raw_html_context(dict(sorted_ranges), html_content)
    
    # 5) Sort issues in each range by end line desc (for diff application)
    for range_key, issues in final_ranges.items():
        issues.sort(key=lambda x: x.get("match_line_end", 0), reverse=True)
    
    return {
        "summary": {
            "total_ranges": len(final_ranges),
            "total_issues": sum(len(issues) for issues in final_ranges.values()),
            "range_sizes": {key: len(issues) for key, issues in final_ranges.items()},
        },
        "line_ranges": final_ranges
    }


def get_line_ranges_for_llm(processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Produce a simplified format suited for LLM processing.
    """
    line_ranges = processed_data.get("line_ranges", {})
    
    llm_inputs = []
    for range_key, issues in line_ranges.items():
        range_info = {
            "line_range": range_key,
            "range_info": {
                "start_line": int(range_key.split('-')[0]),
                "end_line": int(range_key.split('-')[1]),
                "line_count": int(range_key.split('-')[1]) - int(range_key.split('-')[0]) + 1,
                "issue_count": len(issues)
            },
            "issues": []
        }
        
        for issue in issues:
            llm_issue = {
                "audit_id": issue.get("audit_id"),
                "title": issue.get("title"),
                "description": issue.get("description"),
                "match_html": issue.get("match_html"),
                "raw_html": issue.get("raw_html"),
                "match_line_start": issue.get("match_line_start"),
                "match_line_end": issue.get("match_line_end")
            }
            range_info["issues"].append(llm_issue)
        
        llm_inputs.append(range_info)
    
    return llm_inputs


def transform_matched_result(matched_result: Dict[str, Any], html_content: str = None) -> List[Dict[str, Any]]:
    """
    Reformat matched_result into a grouped range structure.
    Output shape example:
    [
        {
            "start_line": 10,
            "end_line": 20,
            "issue_count": 3,
            "section_html": "full HTML slice for 10-20...",
            "issues": [
                {"title": "Links are not crawlable", "raw_html": "<a ...>", "start_line": 13, "end_line": 14}
            ]
        }
    ]
    """
    print(f"🔧 transform_matched_result start...")
    print(f"   - matched_result size: {len(str(matched_result))} chars")
    print(f"   - HTML size: {len(html_content) if html_content else 0} chars")
    
    issues = matched_result.get("issues", [])
    print(f"   - total raw issues: {len(issues)}")
    
    # Count match status
    matched_issues = [it for it in issues if it.get("match_status") == "matched"]
    unmatched_issues = [it for it in issues if it.get("match_status") != "matched"]
    print(f"   - matched issues: {len(matched_issues)}")
    print(f"   - unmatched issues: {len(unmatched_issues)}")
    
    if unmatched_issues:
        print(f"   - unmatched audit_ids sample: {[it.get('audit_id') for it in unmatched_issues[:3]]}")
    
    # 1) group by ranges
    print(f"   - grouping by ranges...")
    line_ranges = extract_line_ranges(issues)
    print(f"   - grouped ranges: {len(line_ranges)}")
    for range_key, range_issues in line_ranges.items():
        print(f"     {range_key}: {len(range_issues)} issues")
    
    # 2) merge overlaps
    print(f"   - merging overlapping ranges...")
    merged_ranges = merge_overlapping_ranges(line_ranges)
    print(f"   - merged ranges: {len(merged_ranges)}")
    for range_key, range_issues in merged_ranges.items():
        print(f"     {range_key}: {len(range_issues)} issues")
    
    # 3) sort by size
    print(f"   - sorting by size...")
    sorted_ranges = sort_ranges_by_size(merged_ranges)
    print(f"   - range order: {[range_key for range_key, _ in sorted_ranges]}")
    
    # details
    print(f"   - range details:")
    for range_key, issues in sorted_ranges:
        start, end = map(int, range_key.split('-'))
        line_count = end - start + 1
        print(f"     {range_key}: {line_count} lines")
    
    # 4) reformat output
    print(f"   - reformating output...")
    result = []
    
    # Maintain sorted order
    for range_key, issues in sorted_ranges:
        start_line, end_line = map(int, range_key.split('-'))
        
        # Extract HTML content for the entire range
        section_html = ""
        if html_content:
            html_lines = html_content.split('\n')
            start_idx = max(0, start_line - 1)  # 1-based to 0-based conversion
            end_idx = min(len(html_lines), end_line)
            section_html = '\n'.join(html_lines[start_idx:end_idx])
            print(f"     {range_key}: extracted HTML {len(section_html)} chars")
        
        # Filter fields per issue
        filtered_issues = []
        for issue in issues:
            filtered_issue = {
                "title": issue.get("title", ""),
                "raw_html": issue.get("match_html", ""),  # Matched specific HTML line
                "start_line": issue.get("match_line_start"),  # Specific line number
                "end_line": issue.get("match_line_end")
            }
            filtered_issues.append(filtered_issue)
        
        # Sort per-issue by end line desc (for diff application)
        filtered_issues.sort(key=lambda x: x.get("end_line", 0), reverse=True)
        
        range_info = {
            "start_line": start_line,
            "end_line": end_line,
            "issue_count": len(filtered_issues),
            "section_html": section_html,  # Complete HTML for entire range
            "issues": filtered_issues
        }
        result.append(range_info)
    
    print(f"   - final ranges: {len(result)}")
    print(f"🔧 transform_matched_result done")
    
    return result


def create_dummy_matched_result() -> Dict[str, Any]:
    """
    Create dummy matched_result data for testing
    Contains overlapping line ranges to test merge logic
    """
    print("🧪 Creating dummy test data...")
    
    dummy_result = {
        "issues": [
            # Issue 1: lines 10-16
            {
                "audit_id": "crawlable-anchors",
                "title": "Links are not crawlable",
                "description": "Links with javascript:void(0) are not crawlable",
                "match_status": "matched",
                "match_html": "<a href=\"javascript:void(0)\">click here</a>",
                "match_line_start": 10,
                "match_line_end": 16
            },
            # Issue 2: lines 13-20 (overlaps with issue 1)
            {
                "audit_id": "image-alt",
                "title": "Image elements do not have [alt] attributes",
                "description": "Images without alt attributes are not accessible",
                "match_status": "matched",
                "match_html": "<img src=\"photo.jpg\" class=\"photo\">",
                "match_line_start": 13,
                "match_line_end": 20
            },
            # Issue 3: lines 25-30
            {
                "audit_id": "duplicate-title",
                "title": "Document has duplicate title",
                "description": "Duplicate titles can confuse search engines",
                "match_status": "matched",
                "match_html": "<title>Duplicate Title</title>",
                "match_line_start": 25,
                "match_line_end": 30
            },
            # Issue 4: lines 28-35 (overlaps with issue 3)
            {
                "audit_id": "meta-description",
                "title": "Document does not have a meta description",
                "description": "Meta descriptions help with SEO",
                "match_status": "matched",
                "match_html": "<meta name=\"description\" content=\"\">",
                "match_line_start": 28,
                "match_line_end": 35
            },
            # Issue 5: lines 40-45 (independent range)
            {
                "audit_id": "hreflang",
                "title": "Document has invalid hreflang",
                "description": "Invalid hreflang attributes",
                "match_status": "matched",
                "match_html": "<link rel=\"alternate\" hreflang=\"xx-YY\">",
                "match_line_start": 40,
                "match_line_end": 45
            },
            # Issue 6: lines 50-60 (large range)
            {
                "audit_id": "large-content",
                "title": "Content is too large",
                "description": "Page content exceeds recommended size",
                "match_status": "matched",
                "match_html": "<div class=\"large-content\">...</div>",
                "match_line_start": 50,
                "match_line_end": 60
            },
            # Issue 7: lines 55-58 (within issue 6 range)
            {
                "audit_id": "small-issue",
                "title": "Small formatting issue",
                "description": "Minor formatting problem",
                "match_status": "matched",
                "match_html": "<span class=\"error\">error</span>",
                "match_line_start": 55,
                "match_line_end": 58
            }
        ]
    }
    
    print(f"✅ Created {len(dummy_result['issues'])} test issues")
    print("   Contains the following overlapping line ranges:")
    print("   - 10-16 and 13-20 → should merge to 10-20")
    print("   - 25-30 and 28-35 → should merge to 25-35") 
    print("   - 50-60 and 55-58 → should merge to 50-60")
    print("   - 40-45 → independent range")
    
    return dummy_result


def test_dummy_data():
    """
    Test dummy data processing logic
    """
    print("\n" + "="*60)
    print("🧪 Testing dummy data processing logic")
    print("="*60)
    
    # Create dummy data
    dummy_result = create_dummy_matched_result()
    
    # Create dummy HTML content
    dummy_html = "\n".join([f"Line {i}: Dummy content for testing" for i in range(1, 61)])
    
    # Process data
    result = transform_matched_result(dummy_result, dummy_html)
    
    # Display results
    print(f"\n📊 Processing results:")
    for i, range_info in enumerate(result, 1):
        print(f"\n{i}. Line range: {range_info['start_line']}-{range_info['end_line']}")
        print(f"   Issue count: {range_info['issue_count']}")
        print(f"   HTML length: {len(range_info['section_html'])} characters")
        print(f"   Specific issues:")
        for j, issue in enumerate(range_info['issues'], 1):
            print(f"     {j}. {issue['title']} (lines {issue['start_line']}-{issue['end_line']})")
            print(f"        HTML: {issue['raw_html']}")
    
    print("\n" + "="*60)
    return result
