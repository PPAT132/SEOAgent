from app.schemas.seo_analysis import SEOAnalysisResult

class HTMLEditor:

    def __init__(self):
        pass
    
    def modify_html(self, html: str, modified_issues: SEOAnalysisResult) -> str:
        seo_score = modified_issues.seo_score
        lines = modified_issues.total_lines
        issues = modified_issues.issues # assuming they are sorted in descending order by line number
        print("lines: ", lines)

        html_index = len(html)-1
        line = lines

        for issue in issues:
            line_end = issue.end_line # inclusive
            line_start = issue.start_line # inclusive

            html_start = 0
            html_end = 0

            while line_start <= line:
                if (html[html_index] == "\n"):
                    if (line == line_end+1):
                        html_end = html_index
                    if (line == line_start):
                        html_start = html_index
                    line -= 1
                html_index -= 1
            print("--------")
            print("line: ", line)
            print("html_index: ", html_index)
            print("html_start: ", html_start)
            print("html_end+1: ", html_end+1)
            html = html[:html_start+1] + issue.optimized_html + html[html_end:]
        return html
                