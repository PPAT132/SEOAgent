# matcher.py
# Map normalized issues back to raw HTML slices and 1-based line numbers.

import re
from typing import Any, Dict, List, Optional, Tuple
from lxml import html, etree
from urllib.parse import urlparse, urljoin, parse_qs

VOID_TAGS = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}

def _normalize_url_for_matching(url: str) -> str:
    """
    Normalize URLs for matching by removing localhost prefixes and normalizing paths.
    This handles cases where Lighthouse service adds http://localhost:3002/ prefix.
    """
    if not url:
        return ""
    
    # Parse the URL
    parsed = urlparse(url)
    
    # If it's a localhost URL, extract just the path
    if parsed.netloc and "localhost" in parsed.netloc:
        return parsed.path or "/"
    
    # If it's a relative path, normalize it
    if not parsed.scheme and not parsed.netloc:
        # Remove leading slash for relative paths
        return parsed.path.lstrip("/") if parsed.path else ""
    
    # For absolute URLs, return as is
    return url

def _urls_match_for_audit(lighthouse_url: str, html_href: str) -> bool:
    """
    Compare URLs for audit matching, handling localhost prefixes and path differences.
    """
    if not lighthouse_url or not html_href:
        return False
    
    # Normalize both URLs
    norm_lighthouse = _normalize_url_for_matching(lighthouse_url)
    norm_html = _normalize_url_for_matching(html_href)
    
    # Direct match
    if norm_lighthouse == norm_html:
        return True
    
    # Handle relative vs absolute path differences
    # e.g., "page.html" vs "/page.html" vs "page.html"
    if norm_lighthouse.startswith("/"):
        norm_lighthouse = norm_lighthouse[1:]
    if norm_html.startswith("/"):
        norm_html = norm_html[1:]
    
    if norm_lighthouse == norm_html:
        return True
    
    # NEW: Handle base href path resolution issues
    # Extract path components for deeper analysis
    lighthouse_path = _extract_path_components(norm_lighthouse)
    html_path = _extract_path_components(norm_html)
    
    # Try to match by path components (ignoring domain differences)
    if _paths_match_by_components(lighthouse_path, html_path):
        return True
    
    # Try to match by filename and query parameters
    if _urls_match_by_filename_and_query(lighthouse_url, html_href):
        return True
    
    return False

def _extract_path_components(url: str) -> dict:
    """
    Extract path components from URL for deeper matching.
    """
    
    parsed = urlparse(url)
    
    # Split path into components
    path_parts = [p for p in parsed.path.split('/') if p]
    
    # Parse query parameters
    query_params = parse_qs(parsed.query)
    
    return {
        'path_parts': path_parts,
        'query_params': query_params,
        'filename': path_parts[-1] if path_parts else '',
        'extension': path_parts[-1].split('.')[-1] if path_parts and '.' in path_parts[-1] else ''
    }

def _paths_match_by_components(lighthouse_path: dict, html_path: dict) -> bool:
    """
    Compare paths by their components, ignoring domain differences.
    """
    # Compare filename
    if lighthouse_path['filename'] and html_path['filename']:
        if lighthouse_path['filename'] == html_path['filename']:
            return True
    
    # Compare path structure (last few components)
    lh_parts = lighthouse_path['path_parts']
    html_parts = html_path['path_parts']
    
    if len(lh_parts) >= 2 and len(html_parts) >= 1:
        # Try to match by end of path
        if lh_parts[-1] == html_parts[-1]:
            return True
    
    return False

def _urls_match_by_filename_and_query(lighthouse_url: str, html_href: str) -> bool:
    """
    Match URLs by filename and query parameters, ignoring domain and path differences.
    """
    
    lh_parsed = urlparse(lighthouse_url)
    html_parsed = urlparse(html_href)
    
    # Extract filename
    lh_filename = lh_parsed.path.split('/')[-1] if lh_parsed.path else ''
    html_filename = html_parsed.path.split('/')[-1] if html_parsed.path else ''
    
    if lh_filename and html_filename and lh_filename == html_filename:
        # If filenames match, also check query parameters
        lh_query = parse_qs(lh_parsed.query)
        html_query = parse_qs(html_parsed.query)
        
        # Compare key query parameters (ignore values that might be different due to base href)
        if set(lh_query.keys()) == set(html_query.keys()):
            return True
    
    return False

def _build_line_index(raw: str) -> List[int]:
    """Prefix array of line-start offsets to convert offsets → 1-based line numbers."""
    starts = [0]
    for i, ch in enumerate(raw):
        if ch == "\n":
            starts.append(i + 1)
    return starts

def _offset_to_line_1based(starts: List[int], offset: int) -> int:
    import bisect
    i = bisect.bisect_right(starts, offset) - 1
    return i + 1  # 1-based

def _slice_to_lines_1based(starts: List[int], s: int, e: int) -> Tuple[int, int]:
    return _offset_to_line_1based(starts, s), _offset_to_line_1based(starts, e)

def _start_tag_regex(tag: str, attrs: Dict[str, str]) -> re.Pattern:
    """
    Build a robust regex for a start-tag with order-insensitive attrs (href/src/id/class/name/etc).
    """
    parts = [rf"<{tag}\b"]
    for k, v in attrs.items():
        v_esc = re.escape(v)
        parts.append(rf"(?=[^>]*\b{k}\s*=\s*(['\"])({v_esc})\1)")
    parts.append(r"[^>]*>")
    return re.compile("".join(parts), re.I | re.S)

def _find_window(raw: str, starts: List[int], prefer_line: Optional[int], lines: int = 80) -> Tuple[int, int]:
    if prefer_line is None:
        return 0, len(raw)
    lo = max(1, prefer_line - lines)
    hi = min(len(starts), prefer_line + lines)
    return starts[lo-1], starts[hi-1] if hi-1 < len(starts) else len(raw)

class _Dom:
    """Thin wrapper over lxml.html tree with helpers."""
    def __init__(self, raw_html: str):
        self.raw = raw_html
        self.starts = _build_line_index(raw_html)
        self.tree = html.fromstring(raw_html)

    def css(self, selector: str):
        try:
            return self.tree.cssselect(selector)
        except Exception:
            return []

    def _children_elements(self, node):
        return [c for c in node if isinstance(c.tag, str)]

    def by_path(self, path: str):
        """
        Lighthouse node.path like:
        "1,HTML,2,BODY,10,TABLE,0,TBODY,0,TR,0,TD,0,DIV,2,A"
        Indices are 0-based among element-children at each level.
        """
        if not path:
            return None
        parts = path.split(",")
        if len(parts) % 2 != 0:
            return None

        node = self.tree.getroottree().getroot()  # <html>
        # Path may start with "1,HTML"; ensure we’re at <html>
        if node.tag.lower() != parts[1].lower():
            html_elems = self.tree.xpath(f"//{parts[1].lower()}")[0:1]
            if not html_elems:
                return None
            node = html_elems[0]

        i = 2
        while i < len(parts):
            idx = int(parts[i]); tag = parts[i+1].lower()
            kids = self._children_elements(node)
            if idx < 0 or idx >= len(kids):
                return None
            node = kids[idx]
            if node.tag.lower() != tag:
                # tolerate parser-inserted wrappers (e.g., tbody)
                alt = None
                for cand in kids[idx: idx+3]:
                    if getattr(cand, "tag", "").lower() == tag:
                        alt = cand; break
                if not alt:
                    return None
                node = alt
            i += 2
        return node

    def map_elem_to_offsets(self, elem, prefer_snippet: Optional[str] = None) -> Optional[Tuple[int, int]]:
        """Map a DOM element back to raw offsets. Prefer exact snippet if provided."""
        raw = self.raw

        # 1) Prefer exact snippet text if present in the raw
        # BUT: Don't use raw.find() directly as it may find wrong occurrence
        # Instead, use sourceline + regex matching for precise location
        if prefer_snippet:
            # Try to find the snippet near the element's sourceline for precision
            prefer_line = getattr(elem, "sourceline", None)
            if prefer_line is not None:
                # Find snippet near the expected line
                w_s, w_e = _find_window(raw, self.starts, prefer_line)
                off = raw.find(prefer_snippet, w_s, w_e)
                if off != -1:
                    return off, off + len(prefer_snippet)
            
            # Fallback: find all occurrences and use context to pick the right one
            all_occurrences = []
            start_pos = 0
            while True:
                off = raw.find(prefer_snippet, start_pos)
                if off == -1:
                    break
                all_occurrences.append(off)
                start_pos = off + 1
            
            if len(all_occurrences) == 1:
                return all_occurrences[0], all_occurrences[0] + len(prefer_snippet)
            elif len(all_occurrences) > 1:
                # Multiple occurrences - need to distinguish
                # Use element's attributes and context to find the right one
                return self._find_best_snippet_match(elem, prefer_snippet, all_occurrences)

        # 2) Otherwise: use sourceline to narrow a start-tag search
        prefer_line = getattr(elem, "sourceline", None)
        tag = elem.tag.lower()
        key_attrs: Dict[str, str] = {}
        for k in ("id","class","href","src","name","content","rel","type","alt","title"):
            if k in elem.attrib:
                key_attrs[k] = elem.attrib[k]

        pat = _start_tag_regex(tag, key_attrs)
        w_s, w_e = _find_window(raw, self.starts, prefer_line)
        m = pat.search(raw, w_s, w_e)
        if not m:
            m = pat.search(raw)
        if not m:
            return None

        s = m.start()
        # void tag?
        if tag in VOID_TAGS or raw[m.end()-2:m.end()] == "/>":
            return s, m.end()

        # find matching closing tag with same-tag nesting
        open_pat  = re.compile(rf"<\s*{tag}\b", re.I)
        close_pat = re.compile(rf"</\s*{tag}\s*>", re.I)
        pos = m.end()
        depth = 1
        while True:
            m_open = open_pat.search(raw, pos)
            m_close = close_pat.search(raw, pos)
            if not m_close:
                return s, m.end()  # fallback: start tag only
            if m_open and m_open.start() < m_close.start():
                depth += 1
                pos = m_open.end()
                continue
            depth -= 1
            pos = m_close.end()
            if depth == 0:
                return s, pos

    def _find_best_snippet_match(self, elem, snippet: str, positions: List[int]) -> Optional[Tuple[int, int]]:
        """
        Choose the best one from multiple snippet positions based on element attributes and context.
        """
        if not positions:
            return None
        
        if len(positions) == 1:
            return positions[0], positions[0] + len(snippet)
        
        # Get element attributes
        elem_attrs = elem.attrib
        elem_tag = elem.tag.lower()
        
        # Get parent element information
        parent = elem.getparent()
        parent_tag = parent.tag.lower() if parent else ""
        parent_id = parent.get("id") if parent else ""
        
        best_position = None
        best_score = 0
        
        for pos in positions:
            score = 0
            
            # Get context for this position
            context_start = max(0, pos - 200)
            context_end = min(len(self.raw), pos + len(snippet) + 200)
            context = self.raw[context_start:context_end]
            
            # 1. Check if parent element ID matches
            if parent_id and parent_id in context:
                score += 10
            
            # 2. Check if parent element tag matches
            if parent_tag and f"<{parent_tag}" in context:
                score += 5
            
            # 3. Check if element tag matches
            if elem_tag and f"<{elem_tag}" in context:
                score += 3
            
            # 4. Check if element attributes match
            for attr_name, attr_value in elem_attrs.items():
                if attr_value and attr_value in context:
                    score += 2
            
            # 5. Check if in the correct section
            if parent_id and "section#" in parent_id:
                if parent_id in context:
                    score += 8
            
            if score > best_score:
                best_score = score
                best_position = pos
        
        # If a high-scoring position is found, use it; otherwise use the first position
        if best_position is not None:
            return best_position, best_position + len(snippet)
        else:
            return positions[0], positions[0] + len(snippet)

# ---------- public API ----------

def match_single_issue(raw_html: str, issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the issue with filled match_* fields if located.
    Strategy:
      node.path -> node.selector -> node.snippet -> url+link_text -> code (minimal)
    """
    dom = _Dom(raw_html)
    raw = dom.raw
    starts = dom.starts

    audit_id = issue.get("audit_id")
    node = issue.get("node") or {}
    selector = node.get("selector")
    path = node.get("path")
    snippet = node.get("snippet")
    link_url = issue.get("url")
    link_text = issue.get("link_text") or ""

    # 1) Prefer node.path for precise element selection
    elem = None
    if path:
        elem = dom.by_path(path)

    # 2) If path lookup failed, use node.selector with smarter disambiguation
    if elem is None and selector:
        cands = dom.css(selector)
        if cands:
            # For link tags, try to match by rel attribute to avoid wrong matches
            if snippet and "rel=" in (snippet or ""):
                # Extract rel attribute from snippet
                rel_match = re.search(r'rel\s*=\s*["\']([^"\']+)["\']', snippet)
                if rel_match:
                    target_rel = rel_match.group(1)
                    # Also extract hreflang and href attributes for precise matching
                    hreflang_match = re.search(r'hreflang\s*=\s*["\']([^"\']+)["\']', snippet)
                    href_match = re.search(r'href\s*=\s*["\']([^"\']+)["\']', snippet)
                    target_hreflang = hreflang_match.group(1) if hreflang_match else None
                    target_href = href_match.group(1) if href_match else None
                    # Try exact rel+hreflang+href
                    for cand in cands:
                        cand_rel = cand.get("rel")
                        cand_hreflang = cand.get("hreflang")
                        cand_href = cand.get("href")
                        if (cand_rel == target_rel and 
                            (target_hreflang is None or cand_hreflang == target_hreflang) and 
                            (target_href is None or cand_href == target_href)):
                            elem = cand
                            break
                    # Fallback rel-only
                    if elem is None:
                        for cand in cands:
                            if cand.get("rel") == target_rel:
                                elem = cand
                                break
                    # Final fallback
                    if elem is None:
                        elem = cands[0]
                else:
                    elem = cands[0]
            else:
                # Try to disambiguate by src/href in snippet
                src_match = re.search(r'src\s*=\s*["\']([^"\']+)["\']', snippet or "")
                href_match = re.search(r'href\s*=\s*["\']([^"\']+)["\']', snippet or "")
                if src_match:
                    target_src = src_match.group(1)
                    for cand in cands:
                        if cand.get("src") == target_src:
                            elem = cand
                            break
                if elem is None and href_match:
                    target_href = href_match.group(1)
                    for cand in cands:
                        if cand.get("href") == target_href:
                            elem = cand
                            break
                if elem is None:
                    elem = cands[0]

    # 3) Map element to raw, preferring snippet if present
    if elem is not None:
        offsets = dom.map_elem_to_offsets(elem, prefer_snippet=snippet)
        if offsets:
            s, e = offsets
            ls, le = _slice_to_lines_1based(starts, s, e)
            frag = raw[s:e]
            # collect all identical occurrences as ranges
            ranges = []
            pos = 0
            while True:
                off_all = raw.find(frag, pos)
                if off_all == -1:
                    break
                ls_a, le_a = _slice_to_lines_1based(starts, off_all, off_all + len(frag))
                ranges.append([ls_a, le_a])
                pos = off_all + 1
            issue.update({
                "match_status": "matched",
                "match_html": frag,
                "match_line_ranges": ranges or [[ls, le]]
            })
            return issue

    # 4) If no element: try snippet exact search (good for node-only items with snippet)
    if snippet:
        # For hreflang and similar audits, we need to find the exact snippet
        # to avoid matching the wrong element
        # Normalize HTML for matching (Lighthouse uses escaped quotes, HTML uses regular quotes)
        normalized_snippet = snippet.replace('\\"', '"').replace("\\'", "'")
        
        # Also normalize self-closing tags (Lighthouse: />, HTML: >)
        normalized_snippet = normalized_snippet.replace(' />', '>').replace('/>', '>')
        
        # Try exact match first
        off = raw.find(snippet)
        if off != -1:
            s, e = off, off + len(snippet)
            ls, le = _slice_to_lines_1based(starts, s, e)
            frag = raw[s:e]
            ranges = []
            pos = 0
            while True:
                off_all = raw.find(frag, pos)
                if off_all == -1:
                    break
                ls_a, le_a = _slice_to_lines_1based(starts, off_all, off_all + len(frag))
                ranges.append([ls_a, le_a])
                pos = off_all + 1
            issue.update({
                "match_status": "matched",
                "match_html": frag,
                "match_line_ranges": ranges or [[ls, le]]
            })
            return issue
        
        # Try normalized snippet if exact match failed
        off = raw.find(normalized_snippet)
        if off != -1:
            s, e = off, off + len(normalized_snippet)
            ls, le = _slice_to_lines_1based(starts, s, e)
            frag = raw[s:e]
            ranges = []
            pos = 0
            while True:
                off_all = raw.find(frag, pos)
                if off_all == -1:
                    break
                ls_a, le_a = _slice_to_lines_1based(starts, off_all, off_all + len(frag))
                ranges.append([ls_a, le_a])
                pos = off_all + 1
            issue.update({
                "match_status": "matched",
                "match_html": frag,
                "match_line_ranges": ranges or [[ls, le]]
            })
            return issue
        
        # Try even more flexible matching by removing whitespace differences
        flexible_snippet = re.sub(r'\s+', ' ', normalized_snippet.strip())
        flexible_html = re.sub(r'\s+', ' ', raw)
        off = flexible_html.find(flexible_snippet)
        if off != -1:
            # Find the corresponding position in original HTML
            # This is approximate but should work for most cases
            original_pos = 0
            flexible_pos = 0
            while flexible_pos < off and original_pos < len(raw):
                if raw[original_pos] == flexible_html[flexible_pos]:
                    flexible_pos += 1
                elif raw[original_pos].isspace() and flexible_html[flexible_pos].isspace():
                    flexible_pos += 1
                original_pos += 1
            
            s = original_pos
            e = s + len(normalized_snippet)
            ls, le = _slice_to_lines_1based(starts, s, e)
            frag = raw[s:e]
            ranges = []
            pos = 0
            while True:
                off_all = raw.find(frag, pos)
                if off_all == -1:
                    break
                ls_a, le_a = _slice_to_lines_1based(starts, off_all, off_all + len(frag))
                ranges.append([ls_a, le_a])
                pos = off_all + 1
            issue.update({
                "match_status": "matched",
                "match_html": frag,
                "match_line_ranges": ranges or [[ls, le]]
            })
            return issue
        
        # NEW: Handle base href and path resolution issues
        # Extract the actual element from snippet and try to find it in HTML
        if "src=" in normalized_snippet or "href=" in normalized_snippet:
            # Extract the attribute value that might have path issues
            src_match = re.search(r'src\s*=\s*["\']([^"\']+)["\']', normalized_snippet)
            href_match = re.search(r'href\s*=\s*["\']([^"\']+)["\']', normalized_snippet)
            
            if src_match or href_match:
                lighthouse_path = (src_match.group(1) if src_match else href_match.group(1))
                
                # Try to find the element by tag type and other attributes
                tag_match = re.search(r'<(\w+)', normalized_snippet)
                if tag_match:
                    tag_name = tag_match.group(1)
                    
                    # Extract other attributes for matching
                    other_attrs = {}
                    for attr_match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']+)["\']', normalized_snippet):
                        attr_name, attr_value = attr_match.groups()
                        if attr_name not in ['src', 'href']:  # Skip the problematic path attribute
                            other_attrs[attr_name] = attr_value
                    
                    # Build a CSS selector that excludes the problematic path
                    selector_parts = [tag_name]
                    for attr_name, attr_value in other_attrs.items():
                        selector_parts.append(f'[{attr_name}="{attr_value}"]')
                    
                    if len(selector_parts) > 1:
                        css_selector = ''.join(selector_parts)
                        try:
                            candidates = dom.css(css_selector)
                            if candidates:
                                # Find the best match by comparing other attributes
                                best_match = None
                                best_score = 0
                                
                                for cand in candidates:
                                    score = 0
                                    for attr_name, attr_value in other_attrs.items():
                                        if cand.get(attr_name) == attr_value:
                                            score += 1
                                    
                                    # Bonus for having the same tag
                                    if cand.tag == tag_name:
                                        score += 1
                                    
                                    if score > best_score:
                                        best_score = score
                                        best_match = cand
                                
                                if best_match is not None and best_score > 0:
                                    offsets = dom.map_elem_to_offsets(best_match)
                                    if offsets:
                                        s, e = offsets
                                        ls, le = _slice_to_lines_1based(starts, s, e)
                                        frag2 = raw[s:e]
                                        ranges2 = []
                                        pos2 = 0
                                        while True:
                                            off_all2 = raw.find(frag2, pos2)
                                            if off_all2 == -1:
                                                break
                                            ls_b, le_b = _slice_to_lines_1based(starts, off_all2, off_all2 + len(frag2))
                                            ranges2.append([ls_b, le_b])
                                            pos2 = off_all2 + 1
                                        issue.update({
                                            "match_status": "matched",
                                            "match_html": frag2,
                                            "match_line_ranges": ranges2 or [[ls, le]]
                                        })
                                        return issue
                        except Exception:
                            pass  # CSS selector failed, continue to next strategy
                    
                    # Fallback: If no other attributes, try to find by tag type and position
                    # This handles cases like <img src="path"> where only src exists
                    if not other_attrs:
                        try:
                            # Try to find all elements of this tag type
                            all_tags = dom.css(tag_name)
                            if all_tags:
                                # For images, try to find by looking at the HTML structure
                                # Since we know the path is wrong due to base href, 
                                # we'll try to find the element by its position in the document
                                
                                # Extract the path from Lighthouse to understand the structure
                                path_parts = []
                                if "path" in issue.get("node", {}):
                                    path_str = issue["node"]["path"]
                                    path_parts = path_str.split(",")
                                
                                # Try to find element by approximate position
                                # Look for elements with similar structure
                                for i, elem in enumerate(all_tags):
                                    try:
                                        # Check if this element is in a similar structural position
                                        offsets = dom.map_elem_to_offsets(elem)
                                        if offsets:
                                            s, e = offsets
                                            ls, le = _slice_to_lines_1based(starts, s, e)
                                            
                                            # For debugging, let's see what we found
                                            found_html = raw[s:e]
                                            
                                            # Check if this looks like the right element
                                            # (same tag, similar structure, no conflicting attributes)
                                            if (elem.tag == tag_name and 
                                                not elem.get("alt") and  # For images without alt
                                                "src=" in found_html):   # Has src attribute
                                                
                                                # Build ranges for all identical occurrences
                                                ranges3 = []
                                                pos3 = 0
                                                while True:
                                                    off_all3 = raw.find(found_html, pos3)
                                                    if off_all3 == -1:
                                                        break
                                                    ls_c, le_c = _slice_to_lines_1based(starts, off_all3, off_all3 + len(found_html))
                                                    ranges3.append([ls_c, le_c])
                                                    pos3 = off_all3 + 1
                                                issue.update({
                                                    "match_status": "matched",
                                                    "match_html": found_html,
                                                    "match_line_ranges": ranges3 or [[ls, le]]
                                                })
                                                return issue
                                    except Exception:
                                        continue
                        except Exception:
                            pass  # Continue to next strategy

    # 5) link-text style: match by href (+ optional exact visible text)
    if link_url:
        anchors = dom.css("a[href]")
        def norm(t: str) -> str:
            return re.sub(r"\s+", " ", (t or "").strip())
        targets = [a for a in anchors if _urls_match_for_audit(link_url, a.get("href","")) and (not link_text or norm(a.text_content()) == norm(link_text))]
        if not targets:
            targets = [a for a in anchors if _urls_match_for_audit(link_url, a.get("href",""))]
        if targets:
            a = targets[0]
            offsets = dom.map_elem_to_offsets(a)
            if offsets:
                s, e = offsets
                ls, le = _slice_to_lines_1based(starts, s, e)
                frag = raw[s:e]
                ranges = []
                pos = 0
                while True:
                    off_all = raw.find(frag, pos)
                    if off_all == -1:
                        break
                    ls_a, le_a = _slice_to_lines_1based(starts, off_all, off_all + len(frag))
                    ranges.append([ls_a, le_a])
                    pos = off_all + 1
                issue.update({
                    "match_status": "matched",
                    "match_html": frag,
                    "match_line_ranges": ranges or [[ls, le]]
                })
                return issue

    # 6) document-level fallbacks (e.g., missing <title> / meta description)
    if audit_id in ("document-title", "meta-description"):
        # Special handling for "does not have" type issues
        if audit_id == "meta-description":
            # For meta description, we want to insert after <title> tag
            try:
                titles = dom.css("head > title")
                if titles:
                    # Found title tag, insert meta description after it
                    offsets = dom.map_elem_to_offsets(titles[0])
                    if offsets:
                        s, e = offsets
                        ls, le = _slice_to_lines_1based(starts, s, e)
                        # Set start_line=0, end_line=0 to indicate "missing" issue
                        # But provide context around title for insertion
                        issue.update({
                            "match_status": "matched",
                            "match_html": raw[s:e],  # This is the title tag context
                            "match_line_ranges": [[ls, le]]
                        })
                        return issue
            except Exception:
                pass
            
            # Fallback: return head context for insertion
            m_open = re.search(r"<head\b[^>]*>", raw, re.I)
            m_close = re.search(r"</head\s*>", raw, re.I)
            if m_open and m_close and m_close.start() > m_open.start():
                s, e = m_open.start(), m_close.end()
                issue.update({
                    "match_status": "matched",
                    "match_html": raw[s:e],
                    "match_line_ranges": [[s, e]]
                })
                return issue

    # 7) Special handling for canonical audit
    if audit_id == "canonical":
        # Look for canonical link tag
        canonical_links = dom.css('link[rel="canonical"]')
        if canonical_links:
            offsets = dom.map_elem_to_offsets(canonical_links[0])
            if offsets:
                s, e = offsets
                ls, le = _slice_to_lines_1based(starts, s, e)
                issue.update({
                    "match_status": "matched",
                    "match_html": raw[s:e],
                    "match_line_ranges": [[ls, le]]
                })
                return issue

    # 8) Minimal code-value fallback: if a literal code snippet is provided
    code = issue.get("code")
    if isinstance(code, str) and code:
        off = raw.find(code)
        if off != -1:
            s, e = off, off + len(code)
            ls, le = _slice_to_lines_1based(starts, s, e)
            issue.update({
                "match_status": "matched",
                "match_html": raw[s:e],
                "match_line_ranges": [[ls, le]]
            })
            return issue

    # not found
    return issue

def match_issues(raw_html: str, parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input:
      raw_html: string of the page HTML
      parsed:  output of LHRTool.parse_lhr_json()

    Output:
      {
        "seo_score": int|None,
        "issues": [ issue-with-match_* ... ]
      }
    """
    out = {"seo_score": parsed.get("seo_score"), "issues": []}
    for issue in parsed.get("issues", []):
        out["issues"].append(match_single_issue(raw_html, issue))
    return out
