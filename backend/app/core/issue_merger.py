#!/usr/bin/env python3
"""
Issue Merger - merge overlapping issues and merge descriptions
"""

from typing import List, Dict, Any, Tuple


def merge_overlapping_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge overlapping issues and combine descriptions.

    Args:
        issues: Original issue list (expects start_line/end_line keys)

    Returns:
        Merged issue list
    """
    if not issues:
        return []
    
    # Sort by start line
    sorted_issues = sorted(issues, key=lambda x: x.get("start_line", 0))
    
    merged_issues = []
    current_issue = None
    
    for issue in sorted_issues:
        if current_issue is None:
            # First issue
            current_issue = {
                "title": issue.get("title", ""),
                "start_line": issue.get("start_line", 0),
                "end_line": issue.get("end_line", 0),
                "raw_html": issue.get("raw_html", ""),
                "descriptions": [issue.get("title", "")]
            }
        else:
            # Check if ranges overlap
            if _issues_overlap(current_issue, issue):
                # Merge overlapping range
                current_issue["start_line"] = min(current_issue["start_line"], issue.get("start_line", 0))
                current_issue["end_line"] = max(current_issue["end_line"], issue.get("end_line", 0))
                current_issue["descriptions"].append(issue.get("title", ""))
                # Merge HTML (prefer the longer snippet)
                if len(issue.get("raw_html", "")) > len(current_issue["raw_html"]):
                    current_issue["raw_html"] = issue.get("raw_html", "")
            else:
                # Not overlapping, push current and start a new one
                merged_issues.append(_finalize_issue(current_issue))
                current_issue = {
                    "title": issue.get("title", ""),
                    "start_line": issue.get("start_line", 0),
                    "end_line": issue.get("end_line", 0),
                    "raw_html": issue.get("raw_html", ""),
                    "descriptions": [issue.get("title", "")]
                }
    
    # Append the final pending issue
    if current_issue:
        merged_issues.append(_finalize_issue(current_issue))
    
    # Sort by end_line desc (to aid diff application from bottom to top)
    merged_issues.sort(key=lambda x: x["end_line"], reverse=True)
    
    return merged_issues


def _issues_overlap(issue1: Dict[str, Any], issue2: Dict[str, Any]) -> bool:
    """Check if two issues' line ranges overlap."""
    start1, end1 = issue1["start_line"], issue1["end_line"]
    start2, end2 = issue2["start_line"], issue2["end_line"]
    
    # Overlap condition: start1 <= end2 and end1 >= start2
    return start1 <= end2 and end1 >= start2


def _finalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Finalize merged issue and build a combined title."""
    descriptions = issue["descriptions"]
    
    if len(descriptions) == 1:
        # Only one description
        final_title = descriptions[0]
    else:
        # Multiple descriptions, merge them
        unique_descriptions = list(set(descriptions))  # de-duplicate
        if len(unique_descriptions) == 1:
            final_title = f"{unique_descriptions[0]} (multiple locations)"
        else:
            final_title = f"Multiple issues: {'; '.join(unique_descriptions[:3])}"
            if len(unique_descriptions) > 3:
                final_title += f" and {len(unique_descriptions)} total"
    
    return {
        "title": final_title,
        "start_line": issue["start_line"],
        "end_line": issue["end_line"],
        "raw_html": issue["raw_html"]
    }


def transform_to_simple_issues(matched_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert matched_result to a simplified list used by the schema.

    Args:
        matched_result: The matcher result containing issue objects

    Returns:
        Simplified merged issue list
    """
    issues = matched_result.get("issues", [])
    
    # Keep only matched issues
    matched_issues = [it for it in issues if it.get("match_status") == "matched"]
    
    # Merge overlapping issues
    merged_issues = merge_overlapping_issues(matched_issues)
    
    return merged_issues


def transform_to_simple_issues_with_insertions(matched_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert matched_result to a simplified list with insertion support.

    Negative line numbers are treated as insert hints by downstream logic.

    Args:
        matched_result: The matcher result containing issue objects

    Returns:
        Simplified issue list (merged positives, plus inserts and zeros)
    """
    issues = matched_result.get("issues", [])
    
    # Keep only matched issues
    matched_issues = [it for it in issues if it.get("match_status") == "matched"]
    
    # Normalize field names to ensure consistency
    normalized_issues = []
    for issue in matched_issues:
        normalized_issue = {
            "title": issue.get("title", ""),
            "start_line": issue.get("match_line_start", 0),
            "end_line": issue.get("match_line_end", 0),
            "raw_html": issue.get("match_html", ""),
            "descriptions": [issue.get("title", "")]
        }
        normalized_issues.append(normalized_issue)
    
    # Merge overlapping issues (only for positive line numbers)
    positive_line_issues = [it for it in normalized_issues 
                           if it.get("start_line", 0) > 0 and it.get("end_line", 0) > 0]
    negative_line_issues = [it for it in normalized_issues 
                           if it.get("start_line", 0) < 0 or it.get("end_line", 0) < 0]
    zero_line_issues = [it for it in normalized_issues 
                        if it.get("start_line", 0) == 0 and it.get("end_line", 0) == 0]
    
    # Merge positive line number issues (replacement operations)
    merged_positive_issues = merge_overlapping_issues(positive_line_issues)
    
    # Combine all issues: merged replacement issues + insertion issues + zero line number issues
    final_issues = merged_positive_issues + negative_line_issues + zero_line_issues
    
    return final_issues
