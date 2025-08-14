from typing import List, Optional
from pydantic import BaseModel

class NodeLocation(BaseModel):
    selector: str
    path: str
    snippet: str
    nodeLabel: str
    lhId: str

class Issue(BaseModel):
    audit_id: str
    title: str
    node: Optional[NodeLocation]
    url: Optional[str]
    link_text: Optional[str]
    code: Optional[str]
    source_location: Optional[str]
    match_status: str
    match_html: str
    match_line_start: int
    match_line_end: int
    optimized_html: Optional[str]

# use this to pass to llm for now since 
class Issues(BaseModel):
    seo_score: int
    issues: List[Issue]

#don't use this for now since only care about matched_results so just use "Issues" class
class IssuesFile(BaseModel):
    parsed_result: Issues
    matched_result: Issues


