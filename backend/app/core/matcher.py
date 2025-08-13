# matcher.py
# Map normalized issues back to raw HTML slices and 1-based line numbers.

import re
from typing import Any, Dict, List, Optional, Tuple
from lxml import html, etree

VOID_TAGS = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}

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
        if prefer_snippet:
            off = raw.find(prefer_snippet)
            if off != -1:
                return off, off + len(prefer_snippet)

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

# ---------- public API ----------

def match_single_issue(raw_html: str, issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the issue with filled match_* fields if located.
    Strategy:
      node.selector -> node.path -> node.snippet -> url+link_text -> code (minimal)
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

    # 1) Prefer node.selector
    elem = None
    if selector:
        cands = dom.css(selector)
        if cands:
            elem = cands[0]

    # 2) Fallback to node.path
    if elem is None and path:
        elem = dom.by_path(path)

    # 3) Map element to raw, preferring snippet if present
    if elem is not None:
        offsets = dom.map_elem_to_offsets(elem, prefer_snippet=snippet)
        if offsets:
            s, e = offsets
            ls, le = _slice_to_lines_1based(starts, s, e)
            issue.update({
                "match_status": "matched",
                "match_html": raw[s:e],
                "match_line_start": ls,
                "match_line_end": le
            })
            return issue

    # 4) If no element: try snippet exact search (good for node-only items with snippet)
    if snippet:
        off = raw.find(snippet)
        if off != -1:
            s, e = off, off + len(snippet)
            ls, le = _slice_to_lines_1based(starts, s, e)
            issue.update({
                "match_status": "matched",
                "match_html": raw[s:e],
                "match_line_start": ls,
                "match_line_end": le
            })
            return issue

    # 5) link-text style: match by href (+ optional exact visible text)
    if link_url:
        anchors = dom.css("a[href]")
        def norm(t: str) -> str:
            return re.sub(r"\s+", " ", (t or "").strip())
        targets = [a for a in anchors if a.get("href","") == link_url and (not link_text or norm(a.text_content()) == norm(link_text))]
        if not targets:
            targets = [a for a in anchors if a.get("href","") == link_url]
        if targets:
            a = targets[0]
            offsets = dom.map_elem_to_offsets(a)
            if offsets:
                s, e = offsets
                ls, le = _slice_to_lines_1based(starts, s, e)
                issue.update({
                    "match_status": "matched",
                    "match_html": raw[s:e],
                    "match_line_start": ls,
                    "match_line_end": le
                })
                return issue

    # 6) document-level fallbacks (e.g., missing <title> / meta description)
    if audit_id in ("document-title", "meta-description"):
        # If title/meta exists, return that; else return <head> as evidence of absence.
        if audit_id == "document-title":
            # Try to find an existing <title>
            try:
                titles = dom.css("head > title")
            except Exception:
                titles = []
            if titles:
                offsets = dom.map_elem_to_offsets(titles[0])
                if offsets:
                    s, e = offsets
                    ls, le = _slice_to_lines_1based(starts, s, e)
                    issue.update({
                        "match_status": "matched",
                        "match_html": raw[s:e],
                        "match_line_start": ls,
                        "match_line_end": le
                    })
                    return issue

        # Return <head> slice as absence-evidence
        m_open = re.search(r"<head\b[^>]*>", raw, re.I)
        m_close = re.search(r"</head\s*>", raw, re.I)
        if m_open and m_close and m_close.start() > m_open.start():
            s, e = m_open.start(), m_close.end()
            ls, le = _slice_to_lines_1based(starts, s, e)
            issue.update({
                "match_status": "matched",
                "match_html": raw[s:e],
                "match_line_start": ls,
                "match_line_end": le
            })
            return issue

    # 7) Minimal code-value fallback: if a literal code snippet is provided
    code = issue.get("code")
    if isinstance(code, str) and code:
        off = raw.find(code)
        if off != -1:
            s, e = off, off + len(code)
            ls, le = _slice_to_lines_1based(starts, s, e)
            issue.update({
                "match_status": "matched",
                "match_html": raw[s:e],
                "match_line_start": ls,
                "match_line_end": le
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
