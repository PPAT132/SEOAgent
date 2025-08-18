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

    def process_missing_elements(self, issues: List[Dict], html_content: str) -> List[Dict]:
        """
        Process missing elements and assign intelligent insertion positions
        """
        for issue in issues:
            audit_id = issue.get('audit_id', '')
            
            # Check if element exists in HTML
            if not self._element_exists(html_content, audit_id):
                # Element is missing, need to insert
                insertion_line = self._find_safe_insertion_position(html_content, audit_id)
                
                # Check if insertion position is safe
                if self._is_valid_html_insertion(html_content, abs(insertion_line)):
                    issue['start_line'] = insertion_line
                    issue['end_line'] = insertion_line
                    issue['raw_html'] = self._get_suggested_html(audit_id)
                else:
                    # Insertion position not safe, mark as 0 (will be handled by matcher)
                    issue['start_line'] = 0
                    issue['end_line'] = 0
                    issue['raw_html'] = self._get_suggested_html(audit_id)
        
        return issues

    def _element_exists(self, html_content: str, audit_id: str) -> bool:
        """Check if element exists in HTML content"""
        if not html_content:
            return False
            
        # Define element selectors for different audit types
        element_selectors = {
            'meta-description': 'meta[name="description"]',
            'document-title': 'title',
            'hreflang': 'link[rel="alternate"][hreflang]',
            'robots-txt': 'meta[name="robots"]',
            'canonical': 'link[rel="canonical"]',
            'og:title': 'meta[property="og:title"]',
            'og:description': 'meta[property="og:description"]',
            'og:type': 'meta[property="og:type"]',
            'twitter:card': 'meta[name="twitter:card"]',
            'viewport': 'meta[name="viewport"]',
            'charset': 'meta[charset]',
            'language': 'html[lang]'
        }
        
        selector = element_selectors.get(audit_id)
        if not selector:
            return False
            
        # Simple check for element existence (basic implementation)
        if audit_id == 'meta-description':
            return 'name="description"' in html_content
        elif audit_id == 'document-title':
            return '<title>' in html_content and '</title>' in html_content
        elif audit_id == 'hreflang':
            return 'hreflang=' in html_content
        elif audit_id == 'canonical':
            return 'rel="canonical"' in html_content
        elif audit_id.startswith('og:'):
            return f'property="{audit_id}"' in html_content
        elif audit_id == 'viewport':
            return 'name="viewport"' in html_content
        elif audit_id == 'charset':
            return 'charset=' in html_content
        elif audit_id == 'language':
            return 'lang=' in html_content
            
        return False

    def _is_valid_html_insertion(self, html_content: str, line_number: int) -> bool:
        """Check if insertion at specified line is safe"""
        lines = html_content.split('\n')
        
        if line_number <= 0 or line_number > len(lines):
            return False
            
        # Convert to 0-based index
        current_line = lines[line_number - 1]
        
        # Check if we're in the middle of a tag
        if '<' in current_line and '>' not in current_line:
            return False  # Tag not closed, can't insert
            
        # Check if we're in the middle of a string
        if current_line.count('"') % 2 != 0:
            return False  # String not closed, can't insert
            
        # Check if we're in the middle of HTML comment
        if '<!--' in current_line and '-->' not in current_line:
            return False  # Comment not closed, can't insert
            
        return True

    def _find_safe_insertion_position(self, html_content: str, issue_type: str) -> int:
        """Find safe insertion position for different issue types"""
        lines = html_content.split('\n')
        
        if issue_type == "meta-description":
            # Strategy 1: Insert after </title>
            for i, line in enumerate(lines):
                if '</title>' in line:
                    return -(i + 2)  # Insert on next line
                    
            # Strategy 2: If no title, insert after <head>
            for i, line in enumerate(lines):
                if '<head>' in line:
                    return -(i + 2)
                    
            # Strategy 3: If neither exists, insert at document beginning
            return -1
            
        elif issue_type == "hreflang":
            # Insert in <head> tag, near meta tags
            for i, line in enumerate(lines):
                if '<meta' in line:
                    return -(i + 2)
                    
            # If no meta tags, insert after head
            for i, line in enumerate(lines):
                if '<head>' in line:
                    return -(i + 2)
                    
            return -1
            
        elif issue_type == "canonical":
            # Insert in <head> tag
            for i, line in enumerate(lines):
                if '<head>' in line:
                    return -(i + 2)
                    
            return -1
            
        elif issue_type.startswith("og:"):
            # Insert in <head> tag, near other meta tags
            for i, line in enumerate(lines):
                if '<meta' in line:
                    return -(i + 2)
                    
            for i, line in enumerate(lines):
                if '<head>' in line:
                    return -(i + 2)
                    
            return -1
            
        elif issue_type == "viewport":
            # Insert in <head> tag, near other meta tags
            for i, line in enumerate(lines):
                if '<meta' in line:
                    return -(i + 2)
                    
            for i, line in enumerate(lines):
                if '<head>' in line:
                    return -(i + 2)
                    
            return -1
            
        elif issue_type == "charset":
            # Insert at the very beginning of <head>
            for i, line in enumerate(lines):
                if '<head>' in line:
                    return -(i + 2)
                    
            return -1
            
        elif issue_type == "language":
            # Insert in <html> tag
            for i, line in enumerate(lines):
                if '<html' in line:
                    return -(i + 1)  # Insert on same line
                    
            return -1
            
        # Default: insert at beginning
        return -1

    def _get_suggested_html(self, audit_id: str) -> str:
        """Get suggested HTML for missing elements"""
        suggestions = {
            'meta-description': '<meta name="description" content="Your page description here">',
            'document-title': '<title>Your Page Title</title>',
            'hreflang': '<link rel="alternate" hreflang="en" href="https://example.com/en/">',
            'canonical': '<link rel="canonical" href="https://example.com/page">',
            'og:title': '<meta property="og:title" content="Your Open Graph Title">',
            'og:description': '<meta property="og:description" content="Your Open Graph Description">',
            'og:type': '<meta property="og:type" content="website">',
            'twitter:card': '<meta name="twitter:card" content="summary">',
            'viewport': '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            'charset': '<meta charset="UTF-8">',
            'language': 'lang="en"'
        }
        
        return suggestions.get(audit_id, f'<!-- Missing {audit_id} element -->')
