#!/usr/bin/env python3
"""
Issue Merger - merge overlapping issues and merge descriptions
"""

from typing import List, Dict, Any, Tuple


def merge_overlapping_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge overlapping issues based on their ranges.
    
    Args:
        issues: Original issue list (expects ranges keys)
    
    Returns:
        List of merged issues
    """
    if not issues:
        return []
    
    # Sort by first range start line for easier merging
    sorted_issues = sorted(issues, key=lambda x: _get_first_range_start(x))
    
    merged_issues = []
    current_issue = None
    
    for issue in sorted_issues:
        if current_issue is None:
            current_issue = issue.copy()
            continue
        
        # Check if current issue overlaps with the next one
        if _issues_overlap(current_issue, issue):
            # Merge the issues
            current_issue = _merge_two_issues(current_issue, issue)
        else:
            # No overlap, finalize current issue and start a new one
            merged_issues.append(_finalize_issue(current_issue))
            current_issue = issue.copy()
    
    # Don't forget the last issue
    if current_issue is not None:
        merged_issues.append(_finalize_issue(current_issue))
    
    # Sort by end line desc (to aid diff application from bottom to top)
    merged_issues.sort(key=lambda x: _get_last_range_end(x), reverse=True)
    
    return merged_issues

def _get_first_range_start(issue: Dict[str, Any]) -> int:
    """Get the start line of the first range"""
    ranges = _get_ranges_from_issue(issue)
    return ranges[0][0] if ranges else 0

def _get_last_range_end(issue: Dict[str, Any]) -> int:
    """Get the end line of the last range"""
    ranges = _get_ranges_from_issue(issue)
    return ranges[-1][1] if ranges else 0

def _issues_overlap(issue1: Dict[str, Any], issue2: Dict[str, Any]) -> bool:
    """Check if two issues overlap based on their ranges"""
    ranges1 = _get_ranges_from_issue(issue1)
    ranges2 = _get_ranges_from_issue(issue2)
    
    for r1 in ranges1:
        for r2 in ranges2:
            start1, end1 = r1
            start2, end2 = r2
            if start1 <= end2 and start2 <= end1:
                return True
    return False

def _merge_two_issues(issue1: Dict[str, Any], issue2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two overlapping issues"""
    merged = issue1.copy()
    
    # Merge ranges
    ranges1 = _get_ranges_from_issue(issue1)
    ranges2 = _get_ranges_from_issue(issue2)
    merged_ranges = _merge_ranges(ranges1, ranges2)
    merged["ranges"] = merged_ranges
    
    # Merge titles (keep both if different)
    title1 = issue1.get("title", "")
    title2 = issue2.get("title", "")
    if title1 != title2:
        merged["title"] = f"{title1}; {title2}"
    
    # Merge raw_html (keep the longer one)
    html1 = issue1.get("raw_html", "")
    html2 = issue2.get("raw_html", "")
    merged["raw_html"] = html1 if len(html1) >= len(html2) else html2
    
    return merged


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
        "raw_html": issue["raw_html"],
        "ranges": _normalize_ranges(issue.get("ranges"))
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
            "raw_html": issue.get("match_html", ""),
            "descriptions": [issue.get("title", "")],
            "ranges": issue.get("match_line_ranges")
        }
        normalized_issues.append(normalized_issue)
    
    # Categorize issues by type
    positive_line_issues = [
        it for it in normalized_issues
        if _has_positive_ranges(it)
    ]
    
    negative_line_issues = [
        it for it in normalized_issues
        if _has_negative_ranges(it)
    ]
    
    zero_line_issues = [
        it for it in normalized_issues
        if _has_zero_ranges(it)
    ]

    # Disable positive merging to keep count = matched
    merged_positive_issues = positive_line_issues
    
    # Combine all issues: merged replacement issues + insertion issues + zero line number issues
    final_issues = merged_positive_issues + negative_line_issues + zero_line_issues
    
    return final_issues


def _get_ranges_from_issue(issue: Dict[str, Any]) -> List[List[int]]:
    ranges = issue.get("ranges") or issue.get("match_line_ranges")
    if isinstance(ranges, list) and ranges:
        # ensure each item is [start, end]
        cleaned = []
        for r in ranges:
            if isinstance(r, (list, tuple)) and len(r) == 2:
                s, e = int(r[0]), int(r[1])
                if s > 0 and e > 0:
                    cleaned.append([s, e])
        return cleaned
    # fallback to single range
    s = int(issue.get("start_line", 0))
    e = int(issue.get("end_line", 0))
    return [[s, e]] if s and e else []


def _merge_ranges(r1: List[List[int]], r2: List[List[int]]) -> List[List[int]]:
    all_ranges = (r1 or []) + (r2 or [])
    if not all_ranges:
        return []
    # sort and merge overlaps/duplicates
    all_ranges.sort(key=lambda x: (x[0], x[1]))
    merged: List[List[int]] = []
    for s, e in all_ranges:
        if not merged or s > merged[-1][1] + 0:
            merged.append([s, e])
        else:
            merged[-1][1] = max(merged[-1][1], e)
    return merged


def _normalize_ranges(ranges: List[List[int]] , s_default: int, e_default: int) -> List[List[int]]:
    if not ranges:
        if s_default or e_default:
            return [[s_default, e_default]]
        return []
    # Deduplicate
    uniq = []
    seen = set()
    for r in ranges:
        key = (int(r[0]), int(r[1]))
        if key not in seen:
            seen.add(key)
            uniq.append([key[0], key[1]])
    return uniq

def _has_positive_ranges(issue: Dict[str, Any]) -> bool:
    """Check if issue has positive ranges"""
    ranges = _get_ranges_from_issue(issue)
    return any(r[0] > 0 and r[1] > 0 for r in ranges)

def _has_negative_ranges(issue: Dict[str, Any]) -> bool:
    """Check if issue has negative ranges"""
    ranges = _get_ranges_from_issue(issue)
    return any(r[0] < 0 or r[1] < 0 for r in ranges)

def _has_zero_ranges(issue: Dict[str, Any]) -> bool:
    """Check if issue has zero ranges"""
    ranges = _get_ranges_from_issue(issue)
    return any(r[0] == 0 and r[1] == 0 for r in ranges)
