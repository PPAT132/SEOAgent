from app.schemas.issues import Issues

class HTMLEditor:

    def __init__(self):
        pass
    
    def modify_html(self, html: str, modified_issues: Issues) -> str:
        seo_score = modified_issues.seo_score
        lines = modified_issues.html_total_lines
        issues = modified_issues.issues # assuming they are sorted in descending order by line number

        html_index = len(html)
        line = lines

        for issue in issues:
            line_end = issues.match_line_end # inclusive
            line_start = issues.match_line_start # inclusive

            html_start = 0
            html_end = 0

            while line_start < line:
                if (html[html_index] == "\n"):
                    line -= 1
                    if (line == line_end):
                        html_end = html_index-1
                    if (line == html_start-1):
                        html_start = html_index+1
                html_index -= 1
            
            html = html[:html_start] + issue.optimized_html + html[html_end+1:]
        
        return html
                