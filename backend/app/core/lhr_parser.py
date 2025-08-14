# lhr_parser.py
# Parse Lighthouse JSON to a normalized list of issues for matcher to consume.

from typing import Any, Dict, List, Optional

class LHRTool:
    """
    Core tool for parsing Lighthouse JSON (SEO).
    This version matches the actual Lighthouse service response structure:
    lhr["audits"] and lhr["seoScore"]
    """

    def parse_lhr_json(self, lhr_json: Dict[str, Any]) -> Dict[str, Any]:
        # seo_score path matches actual Lighthouse service response
        seo_score = lhr_json.get("seoScore")

        audits = lhr_json.get("audits", {})

        issues: List[Dict[str, Any]] = []
        errors: List[str] = []

        for audit_id, audit in audits.items():
            # Check if audit has an error
            score_display_mode = audit.get("scoreDisplayMode")
            if score_display_mode == "error":
                error_msg = audit.get("errorMessage", "Unknown error")
                errors.append(f"{audit_id}: {error_msg}")
                continue
            
            # Special handling for robots-txt audit that may have parsing issues
            if audit_id == "robots-txt":
                details = audit.get("details", {})
                if isinstance(details, dict) and details.get("type") == "table":
                    items = details.get("items", [])
                    # If robots-txt has many "Syntax not understood" errors, skip this audit
                    syntax_errors = [item for item in items if isinstance(item, dict) and 
                                   item.get("message") == "Syntax not understood"]
                    if len(syntax_errors) > 10:
                        continue
            
            # Only keep failing audits (score = 0 or score < 1 for non-binary)
            score = audit.get("score")
            if score is None or score >= 1:
                continue

            title = audit.get("title", "")
            details = audit.get("details", {}) or {}
            items = details.get("items", []) or []

            # If an audit is failing but has no items (e.g. meta-description/doc-title),
            # still emit a placeholder issue so matcher can decide a strategy (like <head> slice).
            if not items:
                issues.append({
                    "audit_id": audit_id,
                    "title": title,
                    "node": None,              # NodeValue
                    "url": None,               # UrlValue
                    "link_text": None,         # Text for LinkValue
                    "code": None,              # CodeValue
                    "source_location": None,   # {url,line,column,original?}
                    "match_status": "unmatched",
                    "match_html": None,
                    "match_line_start": None,
                    "match_line_end": None,
                })
                continue

            for it in items:
                issue = {
                    "audit_id": audit_id,
                    "title": title,
                    "node": None,
                    "url": None,
                    "link_text": None,
                    "code": None,
                    "source_location": None,
                    "match_status": "unmatched",
                    "match_html": None,
                    "match_line_start": None,
                    "match_line_end": None,
                }

                # NodeValue (e.g. image-alt / crawlable-anchors / document-title)
                node = it.get("node")
                if isinstance(node, dict):
                    issue["node"] = {
                        "selector": node.get("selector"),
                        "path": node.get("path"),
                        "snippet": node.get("snippet"),
                        "nodeLabel": node.get("nodeLabel"),
                        "lhId": node.get("lhId"),
                    }

                # Handle source field that may contain a node object (e.g., is-crawlable audit)
                source = it.get("source")
                if isinstance(source, dict) and source.get("type") == "node":
                    # If we don't already have a node, use the source node
                    if not issue["node"]:
                        issue["node"] = {
                            "selector": source.get("selector"),
                            "path": source.get("path"),
                            "snippet": source.get("snippet"),
                            "nodeLabel": source.get("nodeLabel"),
                            "lhId": source.get("lhId"),
                        }
                elif isinstance(source, str):
                    # CodeValue (e.g. directives or <link rel=alternate ...> etc.)
                    issue["code"] = source

                # Handle subItems for detailed problem reasons (e.g., hreflang audit)
                sub_items = it.get("subItems", {})
                if isinstance(sub_items, dict) and sub_items.get("type") == "subitems":
                    reasons = sub_items.get("items", [])
                    if reasons:
                        # Extract all reason texts
                        reason_texts = []
                        for reason_item in reasons:
                            if isinstance(reason_item, dict) and "reason" in reason_item:
                                reason_texts.append(reason_item["reason"])
                        if reason_texts:
                            issue["code"] = "; ".join(reason_texts)

                # Link-text style: columns "href" + "text"
                if "href" in it:
                    issue["url"] = it.get("href")
                if "text" in it:
                    issue["link_text"] = it.get("text")

                # SourceLocationValue (occasionally appears in other audits)
                if isinstance(it.get("url"), str) and any(k in it for k in ("line", "column", "original")):
                    issue["source_location"] = {
                        "url": it.get("url"),
                        "line": it.get("line"),
                        "column": it.get("column"),
                        "original": it.get("original"),
                    }

                issues.append(issue)

        result = {"seo_score": seo_score, "issues": issues}
        if errors:
            result["errors"] = errors
            result["error_summary"] = f"Lighthouse encountered {len(errors)} errors during analysis"
            
        return result
