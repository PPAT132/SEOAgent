#!/usr/bin/env python3
"""
Issue Merger - 合并重叠的问题，合并错误描述
"""

from typing import List, Dict, Any, Tuple


def merge_overlapping_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    合并重叠的问题，合并错误描述
    
    Args:
        issues: 原始问题列表
        
    Returns:
        合并后的问题列表
    """
    if not issues:
        return []
    
    # 按起始行排序
    sorted_issues = sorted(issues, key=lambda x: x.get("start_line", 0))
    
    merged_issues = []
    current_issue = None
    
    for issue in sorted_issues:
        if current_issue is None:
            # 第一个问题
            current_issue = {
                "title": issue.get("title", ""),
                "start_line": issue.get("start_line", 0),
                "end_line": issue.get("end_line", 0),
                "raw_html": issue.get("raw_html", ""),
                "descriptions": [issue.get("title", "")]
            }
        else:
            # 检查是否重叠
            if _issues_overlap(current_issue, issue):
                # 合并重叠的问题
                current_issue["start_line"] = min(current_issue["start_line"], issue.get("start_line", 0))
                current_issue["end_line"] = max(current_issue["end_line"], issue.get("end_line", 0))
                current_issue["descriptions"].append(issue.get("title", ""))
                # 合并HTML（取较长的那个）
                if len(issue.get("raw_html", "")) > len(current_issue["raw_html"]):
                    current_issue["raw_html"] = issue.get("raw_html", "")
            else:
                # 不重叠，保存当前问题，开始新问题
                merged_issues.append(_finalize_issue(current_issue))
                current_issue = {
                    "title": issue.get("title", ""),
                    "start_line": issue.get("start_line", 0),
                    "end_line": issue.get("end_line", 0),
                    "raw_html": issue.get("raw_html", ""),
                    "descriptions": [issue.get("title", "")]
                }
    
    # 添加最后一个问题
    if current_issue:
        merged_issues.append(_finalize_issue(current_issue))
    
    # 按结束行号从大到小排序（为了diff checker）
    merged_issues.sort(key=lambda x: x["end_line"], reverse=True)
    
    return merged_issues


def _issues_overlap(issue1: Dict[str, Any], issue2: Dict[str, Any]) -> bool:
    """检查两个问题是否重叠"""
    start1, end1 = issue1["start_line"], issue1["end_line"]
    start2, end2 = issue2["start_line"], issue2["end_line"]
    
    # 重叠条件：一个范围的起始行 <= 另一个范围的结束行，且一个范围的结束行 >= 另一个范围的起始行
    return start1 <= end2 and end1 >= start2


def _finalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """最终化问题，合并描述"""
    descriptions = issue["descriptions"]
    
    if len(descriptions) == 1:
        # 只有一个描述
        final_title = descriptions[0]
    else:
        # 多个描述，合并它们
        unique_descriptions = list(set(descriptions))  # 去重
        if len(unique_descriptions) == 1:
            final_title = f"{unique_descriptions[0]} (多个位置)"
        else:
            final_title = f"多个问题: {'; '.join(unique_descriptions[:3])}"  # 最多显示3个
            if len(unique_descriptions) > 3:
                final_title += f" 等{len(unique_descriptions)}个问题"
    
    return {
        "title": final_title,
        "start_line": issue["start_line"],
        "end_line": issue["end_line"],
        "raw_html": issue["raw_html"]
    }


def transform_to_simple_issues(matched_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    将 matched_result 转换为简单的 IssueInfo 格式
    
    Args:
        matched_result: 匹配结果
        
    Returns:
        简单的问题列表
    """
    issues = matched_result.get("issues", [])
    
    # 只保留已匹配的问题
    matched_issues = [it for it in issues if it.get("match_status") == "matched"]
    
    # 合并重叠问题
    merged_issues = merge_overlapping_issues(matched_issues)
    
    return merged_issues


def transform_to_simple_issues_with_insertions(matched_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    将 matched_result 转换为简单的 IssueInfo 格式，支持插入操作
    
    Args:
        matched_result: 匹配结果
        
    Returns:
        简单的问题列表，负数行号表示插入
    """
    issues = matched_result.get("issues", [])
    
    # 只保留已匹配的问题
    matched_issues = [it for it in issues if it.get("match_status") == "matched"]
    
    # 标准化字段名，确保一致性
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
    
    # 合并重叠问题（只对正数行号的问题）
    positive_line_issues = [it for it in normalized_issues 
                           if it.get("start_line", 0) > 0 and it.get("end_line", 0) > 0]
    negative_line_issues = [it for it in normalized_issues 
                           if it.get("start_line", 0) < 0 or it.get("end_line", 0) < 0]
    zero_line_issues = [it for it in normalized_issues 
                        if it.get("start_line", 0) == 0 and it.get("end_line", 0) == 0]
    
    # 合并正数行号的问题（替换操作）
    merged_positive_issues = merge_overlapping_issues(positive_line_issues)
    
    # 组合所有问题：合并后的替换问题 + 插入问题 + 零行号问题
    final_issues = merged_positive_issues + negative_line_issues + zero_line_issues
    
    return final_issues
