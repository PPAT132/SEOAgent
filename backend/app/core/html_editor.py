from typing import List
import re
from app.schemas.seo_analysis import SEOAnalysisResult

class HTMLEditor:

    def __init__(self):
        # Lazy load ImageCaptioner to avoid import issues if dependencies aren't installed
        self._image_captioner = None
    
    def _get_image_captioner(self):
        """Lazy load the ImageCaptioner to avoid import errors if dependencies missing"""
        if self._image_captioner is None:
            try:
                from app.core.image_captioner import ImageCaptioner
                self._image_captioner = ImageCaptioner()
                print("✓ ImageCaptioner loaded successfully")
            except ImportError as e:
                print(f"⚠️  ImageCaptioner not available: {e}")
                self._image_captioner = False  # Mark as unavailable
            except Exception as e:
                print(f"⚠️  Failed to initialize ImageCaptioner: {e}")
                self._image_captioner = False
        return self._image_captioner if self._image_captioner is not False else None
    
    def _replace_unknown_image_alts(self, html_content: str) -> str:
        """
        Replace UNKNOWN_IMAGE alt attributes with AI-generated captions
        
        Args:
            html_content: HTML content that may contain UNKNOWN_IMAGE alt attributes
            
        Returns:
            HTML content with UNKNOWN_IMAGE replaced by actual captions
        """
        if 'UNKNOWN_IMAGE' not in html_content:
            return html_content
        
        print("🖼️  Found UNKNOWN_IMAGE placeholder(s), generating captions...")
        
        # Get the image captioner
        captioner = self._get_image_captioner()
        if not captioner:
            print("⚠️  ImageCaptioner not available, keeping UNKNOWN_IMAGE placeholders")
            return html_content
        
        # Find all img tags with UNKNOWN_IMAGE alt attributes
        img_pattern = r'<img([^>]*?)alt=["\']UNKNOWN_IMAGE["\']([^>]*?)>'
        
        def replace_unknown_alt(match):
            before_alt = match.group(1)
            after_alt = match.group(2)
            full_tag = match.group(0)
            
            # Extract src attribute from the img tag
            src_match = re.search(r'src=["\']([^"\']+)["\']', full_tag)
            if not src_match:
                print("⚠️  No src found in img tag, keeping UNKNOWN_IMAGE")
                return full_tag
            
            src_url = src_match.group(1)
            print(f"🔍 Generating caption for: {src_url}")
            
            try:
                # Generate caption using ImageCaptioner with timeout protection
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Caption generation timed out")
                
                # Set a 10-second timeout for caption generation
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(10)
                
                try:
                    caption = captioner.generate_short_caption(src_url)
                    signal.alarm(0)  # Cancel the alarm
                    
                    if caption:
                        print(f"✓ Generated caption: '{caption}'")
                        # Replace UNKNOWN_IMAGE with the generated caption
                        new_tag = f'<img{before_alt}alt="{caption}"{after_alt}>'
                        return new_tag
                    else:
                        print("⚠️  Failed to generate caption, using URL-based fallback")
                        # Extract descriptive text from URL
                        fallback_alt = self._extract_descriptive_alt_from_url(src_url)
                        new_tag = f'<img{before_alt}alt="{fallback_alt}"{after_alt}>'
                        return new_tag
                        
                except TimeoutError:
                    signal.alarm(0)  # Cancel the alarm
                    print("⚠️  Caption generation timed out, using URL-based fallback")
                    fallback_alt = self._extract_descriptive_alt_from_url(src_url)
                    new_tag = f'<img{before_alt}alt="{fallback_alt}"{after_alt}>'
                    return new_tag
                    
            except Exception as e:
                print(f"⚠️  Error generating caption: {e}")
                # Extract descriptive text from URL as fallback
                fallback_alt = self._extract_descriptive_alt_from_url(src_url)
                new_tag = f'<img{before_alt}alt="{fallback_alt}"{after_alt}>'
                return new_tag
        
        # Replace all UNKNOWN_IMAGE instances
        updated_html = re.sub(img_pattern, replace_unknown_alt, html_content, flags=re.IGNORECASE)
        
        # Count how many were replaced
        original_count = html_content.count('UNKNOWN_IMAGE')
        remaining_count = updated_html.count('UNKNOWN_IMAGE')
        replaced_count = original_count - remaining_count
        
        if replaced_count > 0:
            print(f"✓ Replaced {replaced_count} UNKNOWN_IMAGE placeholder(s) with AI captions")
        
        return updated_html
    
    def _extract_descriptive_alt_from_url(self, url: str) -> str:
        """
        Extract descriptive alt text from image URL
        
        Args:
            url: Image URL or path
            
        Returns:
            Descriptive alt text based on URL
        """
        try:
            # Extract filename from URL
            filename = url.split('/')[-1].split('.')[0]  # Get filename without extension
            
            # Convert filename to readable text
            # Replace common separators with spaces
            descriptive = filename.replace('-', ' ').replace('_', ' ').replace('.', ' ')
            
            # Capitalize first letter of each word
            descriptive = descriptive.title()
            
            # Clean up multiple spaces
            descriptive = ' '.join(descriptive.split())
            
            # If it's too long, truncate
            if len(descriptive) > 50:
                descriptive = descriptive[:47] + "..."
            
            # If empty or too short, use a default
            if len(descriptive) < 3:
                descriptive = "Image"
                
            return descriptive
            
        except Exception as e:
            print(f"⚠️  Error extracting alt from URL: {e}")
            return "Image"
    
    def modify_html(self, html: str, modified_issues: SEOAnalysisResult) -> str:
        """
        Modify HTML content based on SEO issues
        """
        print(f"HTML editing start...")
        print(f"  Original HTML size: {len(html)} characters")
        print(f"  Issues to process: {len(modified_issues.issues)}")
        
        # Split HTML into lines for easier manipulation
        lines = html.split('\n')
        total_lines = len(lines)
        
        # Process issues (no need to sort since we handle ranges internally)
        for i, issue in enumerate(modified_issues.issues):
            print(f"Processing issue {i+1}: {issue.title}")
            print(f"  Original: {issue.raw_html[:100]}...")
            print(f"  Optimized: {issue.optimized_html[:100]}...")
            
            # Handle missing issues (ranges with negative values)
            if all(r[0] < 0 for r in (issue.ranges or [])):
                # Insertion logic using first negative range as position
                insertion_line = abs(issue.ranges[0][0]) if issue.ranges else 1
                processed_payload = self._replace_unknown_image_alts(issue.optimized_html)
                lines.insert(insertion_line - 1, processed_payload)
                continue
            
            # Normal replacement using ranges
            ranges = issue.ranges or []
            sorted_ranges = sorted(ranges, key=lambda r: r[1], reverse=True)
            processed_optimized_html = self._replace_unknown_image_alts(issue.optimized_html)
            optimized_lines = processed_optimized_html.split('\n')
            
            for r_start, r_end in sorted_ranges:
                start_line = r_start - 1
                end_line = r_end - 1
                if start_line < 0 or end_line >= total_lines or start_line > end_line:
                    continue
                lines[start_line:end_line + 1] = optimized_lines
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
                