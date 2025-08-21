from typing import List
from app.schemas.seo_analysis import SEOAnalysisResult

class HTMLEditor:

    def __init__(self):
        pass
    
    def modify_html(self, html: str, modified_issues: SEOAnalysisResult) -> str:
        """
        Modify HTML by replacing issues with optimized HTML.
        Issues should be sorted in descending order by line number to avoid offset issues.
        """
        if not modified_issues.issues:
            return html
            
        # Convert HTML to lines for easier manipulation
        lines = html.split('\n')
        total_lines = len(lines)
        
        print(f"Total lines in HTML: {total_lines}")
        print(f"Number of issues to fix: {len(modified_issues.issues)}")
        
        # Sort issues by line number in descending order to avoid offset issues
        sorted_issues = sorted(modified_issues.issues, key=lambda x: x.end_line, reverse=True)
        
        for i, issue in enumerate(sorted_issues):
            print(f"Processing issue {i+1}: {issue.title}")
            print(f"  Original: {issue.raw_html[:100]}...")
            print(f"  Optimized: {issue.optimized_html[:100]}...")
            
            # Special handling for "does not have" issues (start_line=0, end_line=0)
            if issue.start_line == 0 and issue.end_line == 0:
                print(f"  🔧 This is a 'missing' issue, need to insert content")
                action = self._parse_ai_action(issue.optimized_html)
                html_payload = action.get('html', '')
                mode = action.get('mode', 'INSERT')
                where = action.get('WHERE')
                target = action.get('TARGET')
                attr = action.get('ATTR')

                if mode == 'MODIFY_TAG' and (target or '').lower() == 'html' and attr:
                    # modify <html ...> attributes
                    print(f"  ✏️  Modifying <html> tag attrs: {attr}")
                    for i, line in enumerate(lines):
                        if '<html' in line:
                            # naive append/replace of attribute
                            if '>' in line:
                                insert_pos = line.find('>')
                                new_line = line[:insert_pos] + f" {attr}" + line[insert_pos:]
                                lines[i] = new_line
                                break
                    continue

                # derive default WHERE by heuristic if not provided
                if not where:
                    title_l = (issue.title or '').lower()
                    if 'meta description' in title_l:
                        where = 'after_title'
                    elif 'title' in title_l:
                        where = 'after_meta_charset'
                    elif 'canonical' in title_l:
                        where = 'head_end'
                    elif 'viewport' in title_l:
                        where = 'after_meta_charset'
                    else:
                        where = 'head_start'

                # default: INSERT
                insertion_idx = self._find_insertion_line(lines, where or '')
                print(f"  📍 Inserting at line {insertion_idx + 1} (where={where})")
                if html_payload:
                    for snippet_line in html_payload.split('\n'):
                        lines.insert(insertion_idx, snippet_line)
                        insertion_idx += 1
                    total_lines = len(lines)
                continue
            
            # Normal replacement logic for existing issues
            start_line = issue.start_line - 1  # Convert to 0-based index
            end_line = issue.end_line - 1      # Convert to 0-based index
            
            print(f"  Lines {start_line+1}-{end_line+1}")
            
            # Validate line numbers
            if start_line < 0 or end_line >= total_lines:
                print(f"  ⚠️  Invalid line numbers: {start_line+1}-{end_line+1}, skipping")
                continue
                
            if start_line > end_line:
                print(f"  ⚠️  Start line > end line: {start_line+1} > {end_line+1}, skipping")
                continue
            
            # Replace the lines
            original_lines = lines[start_line:end_line + 1]
            optimized_lines = issue.optimized_html.split('\n')
            
            print(f"  Replacing {len(original_lines)} lines with {len(optimized_lines)} lines")
            
            # Replace the lines
            lines[start_line:end_line + 1] = optimized_lines
            
            # Update total lines count
            total_lines = len(lines)
        
        # Join lines back into HTML
        result_html = '\n'.join(lines)
        
        print(f"HTML editing completed. Final size: {len(result_html)} characters")
        return result_html
    
    def _find_title_line(self, lines: List[str]) -> int:
        """Find the line number of the title tag"""
        for i, line in enumerate(lines):
            if '<title>' in line:
                return i
        return -1

    # Parse AI action header if present
    def _parse_ai_action(self, html_snippet: str) -> dict:
        """Parse <!--AI-ACTION: ...--> header and return dict of directives"""
        import re
        m = re.match(r"\s*<!--\s*AI-ACTION:\s*([^>]+?)-->\s*(.*)$", html_snippet, re.I | re.S)
        if not m:
            return {"mode": "RAW", "html": html_snippet.strip()}
        header, rest = m.group(1), m.group(2)
        directives = {"mode": "RAW", "html": rest.strip()}
        # Split fields like KEY: value; KEY2: value2
        for part in header.split(';'):
            kv = part.strip().split(':', 1)
            if len(kv) == 2:
                key, val = kv[0].strip().upper(), kv[1].strip()
                directives[key] = val
        # Normalize
        if 'INSERT' in directives.get('AI-ACTION', '').upper() or directives.get('MODE') == 'INSERT':
            directives['mode'] = 'INSERT'
        if 'REPLACE' in directives.get('AI-ACTION', '').upper() or directives.get('MODE') == 'REPLACE':
            directives['mode'] = 'REPLACE'
        if 'MODIFY_TAG' in directives.get('AI-ACTION', '').upper() or directives.get('MODE') == 'MODIFY_TAG':
            directives['mode'] = 'MODIFY_TAG'
        return directives

    def _find_head_boundaries(self, lines: List[str]) -> tuple:
        head_start, head_end = -1, -1
        for i, line in enumerate(lines):
            if head_start == -1 and '<head' in line:
                head_start = i
            if '</head>' in line:
                head_end = i
                break
        return head_start, head_end

    def _find_insertion_line(self, lines: List[str], where: str) -> int:
        where = (where or '').lower()
        head_start, head_end = self._find_head_boundaries(lines)
        # helpers
        def find_line(substr: str) -> int:
            for i, line in enumerate(lines):
                if substr.lower() in line.lower():
                    return i
            return -1
        if where == 'after_title':
            t = self._find_title_line(lines)
            return t if t == -1 else t + 1
        if where == 'after_meta_charset':
            m = find_line('<meta charset')
            return m if m == -1 else m + 1
        if where == 'after_meta_viewport':
            m = find_line('name="viewport"')
            return m if m == -1 else m + 1
        if where == 'after_canonical':
            m = find_line('rel="canonical"')
            return m if m == -1 else m + 1
        if where == 'head_start':
            return head_start + 1 if head_start != -1 else 0
        if where == 'head_end':
            return head_end if head_end != -1 else len(lines)
        # default fallback
        return head_start + 1 if head_start != -1 else 0
                