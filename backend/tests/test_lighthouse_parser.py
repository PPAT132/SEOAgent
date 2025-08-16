#!/usr/bin/env python3
"""
Test script for Lighthouse Parser + Matcher (normalized issues pipeline)

This script:
1) Reads the test HTML file
2) Sends it to Lighthouse service for analysis
3) Runs the parser (LHRTool.parse_lhr_json) to normalize issues
4) Runs the matcher (match_issues) to map issues back to raw HTML slices with line numbers
5) Generates a detailed JSON report
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Any, Dict, List

# Make app/core importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'core'))

# NEW: matcher API is match_issues (not locate_all)
from lhr_parser import LHRTool
from matcher import match_issues


class LighthouseParserTester:
    def __init__(self, lighthouse_url: str = "http://localhost:3001"):
        self.lighthouse_url = lighthouse_url
        self.parser = LHRTool()

    # ---------- helpers ----------
    def _extract_seo_score_from_service(self, result: Dict[str, Any]):
        """
        Lighthouse service may return 'seoScore' at top-level,
        or only inside lighthouse_data.result.seo_score depending on your server.
        We try both for logging convenience.
        """
        if isinstance(result, dict):
            if "seoScore" in result:
                return result.get("seoScore")
            ld = result.get("lighthouse_data", {}).get("result", {})
            if "seo_score" in ld:
                return ld.get("seo_score")
        return None

    # ---------- steps ----------
    def read_test_html(self, html_file_path: str):
        """Read the test HTML file."""
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ HTML file not found: {html_file_path}")
            return None
        except Exception as e:
            print(f"❌ Error reading HTML file: {e}")
            return None

    def call_lighthouse_service(self, html_content: str):
        """Call the Lighthouse service to analyze the HTML."""
        print("🔄 Calling Lighthouse service...")
        try:
            resp = requests.post(
                f"{self.lighthouse_url}/audit-html",
                json={"html": html_content},
                timeout=60
            )
            if resp.status_code != 200:
                print(f"❌ Lighthouse service error: {resp.status_code}")
                print(f"Response: {resp.text}")
                return None

            result = resp.json()
            score = self._extract_seo_score_from_service(result)
            print(f"✅ Lighthouse analysis completed! SEO Score: {score if score is not None else 'N/A'}")
            return result

        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to Lighthouse service at {self.lighthouse_url}")
            print("Make sure the Lighthouse service is running on port 3001")
            return None
        except requests.exceptions.Timeout:
            print("❌ Lighthouse service timeout")
            return None
        except Exception as e:
            print(f"❌ Error calling Lighthouse service: {e}")
            return None

    def run_parser(self, lighthouse_result: Dict[str, Any]):
        """Run the parser on Lighthouse results to produce normalized issues."""
        print("🔄 Running LHR parser (normalize issues)...")
        try:
            parsed = self.parser.parse_lhr_json(lighthouse_result)
            issues = parsed.get("issues", []) or []
            print(f"✅ Parser completed! Normalized issues: {len(issues)}")
            return parsed
        except Exception as e:
            print(f"❌ Parser error: {e}")
            import traceback; traceback.print_exc()
            return None

    def run_matcher(self, html_content: str, parsed_result: Dict[str, Any]):
        """
        Run matcher to locate issues in the original HTML.
        NEW API: match_issues(html, parsed_result) -> {"seo_score", "issues":[...with match_*]}
        """
        print("🔄 Running matcher to locate issues in HTML...")
        try:
            matched = match_issues(html_content, parsed_result)
            matched_issues = [it for it in matched.get("issues", []) if it.get("match_status") == "matched"]
            print(f"✅ Matcher completed! Located {len(matched_issues)} / {len(matched.get('issues', []))} issues")
            return matched
        except Exception as e:
            print(f"❌ Matcher error: {e}")
            import traceback; traceback.print_exc()
            return None

    def generate_report(self,
                        lighthouse_result: Dict[str, Any],
                        parsed_result: Dict[str, Any],
                        matched_result: Dict[str, Any],
                        html_file_path: str):
        """Generate a detailed report JSON with line numbers."""
        print("🔄 Generating detailed report with line numbers...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"lighthouse_parser_test_result_{timestamp}.json"

        parsed_issues = parsed_result.get("issues", []) if parsed_result else []
        matched_issues = matched_result.get("issues", []) if matched_result else []

        matched_count = sum(1 for it in matched_issues if it.get("match_status") == "matched")

        # Aggregate by audit_id
        issue_types: Dict[str, Dict[str, int]] = {}
        for it in parsed_issues:
            aid = it.get("audit_id", "unknown")
            issue_types.setdefault(aid, {"total": 0, "matched": 0})
            issue_types[aid]["total"] += 1
        for it in matched_issues:
            if it.get("match_status") == "matched":
                aid = it.get("audit_id", "unknown")
                issue_types.setdefault(aid, {"total": 0, "matched": 0})
                issue_types[aid]["matched"] += 1

        report = {
            "test_info": {
                "timestamp": timestamp,
                "html_file": html_file_path,
                "lighthouse_service_url": self.lighthouse_url
            },
            "lighthouse_raw": lighthouse_result,   # keep the full raw result for inspection
            "parsed_result": parsed_result,         # {"seo_score", "issues":[...]}
            "matched_result": matched_result,       # {"seo_score", "issues":[...with match_*]}
            "summary": {
                "seo_score": parsed_result.get("seo_score") if parsed_result else None,
                "total_issues": len(parsed_issues),
                "matched_issues": matched_count,
                "by_audit": issue_types
            }
        }

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✅ Report saved to: {report_file}")
            return report_file
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return None

    def print_summary(self, parsed_result: Dict[str, Any], matched_result: Dict[str, Any]):
        """Pretty print a short summary in console."""
        if not parsed_result:
            return

        print("\n" + "="*60)
        print("📊 PARSER + MATCHER RESULTS SUMMARY")
        print("="*60)

        seo_score = parsed_result.get("seo_score", "N/A")
        parsed_issues = parsed_result.get("issues", []) or []
        matched_issues = matched_result.get("issues", []) or []

        print(f"SEO Score: {seo_score}")
        print(f"Total Issues Found (normalized): {len(parsed_issues)}")

        matched_count = sum(1 for it in matched_issues if it.get("match_status") == "matched")
        print(f"Issues Located in HTML: {matched_count}")

        # Summarize by audit type
        by_audit: Dict[str, List[Dict[str, Any]]] = {}
        for it in matched_issues:
            by_audit.setdefault(it.get("audit_id", "unknown"), []).append(it)

        if by_audit:
            print("\nIssue Types and Sample Locations:")
            for audit_id in sorted(by_audit.keys()):
                arr = by_audit[audit_id]
                print(f"  • {audit_id}: {len(arr)} located")
                for i, hit in enumerate(arr[:3], 1):
                    ls = hit.get("match_line_start", "N/A")
                    le = hit.get("match_line_end", "N/A")
                    via = hit.get("match_status", "matched")
                    print(f"    [{i}] Lines {ls}-{le} via {via}")
                    html_preview = (hit.get("match_html") or "")
                    if len(html_preview) > 80:
                        html_preview = html_preview[:80] + "..."
                    if html_preview:
                        print(f"       HTML: {html_preview}")

        print("="*60)

    def run_full_test(self, html_file_path: str):
        """Run the complete test pipeline."""
        print("🚀 Starting Lighthouse Parser + Matcher Test")
        print("="*60)

        # Step 1: read HTML
        print(f"📄 Reading HTML file: {html_file_path}")
        html_content = self.read_test_html(html_file_path)
        if not html_content:
            return False
        print(f"✅ HTML loaded ({len(html_content)} characters)")

        # Step 2: Lighthouse service
        lighthouse_result = self.call_lighthouse_service(html_content)
        if not lighthouse_result:
            return False

        # Step 3: Parser (normalize issues)
        parsed_result = self.run_parser(lighthouse_result)
        if not parsed_result:
            return False

        # Step 4: Matcher (map to raw lines)
        matched_result = self.run_matcher(html_content, parsed_result)
        if not matched_result:
            return False

        # Step 5: Report
        report_file = self.generate_report(lighthouse_result, parsed_result, matched_result, html_file_path)

        # Step 6: Console summary
        self.print_summary(parsed_result, matched_result)

        if report_file:
            print(f"\n📋 Full detailed report saved to: {report_file}")
            print("Open it to inspect all parsed + matched data.")
        return True


def main():
    """Main entry."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_html_file = os.path.join(script_dir, "test_seo_page.html")

    if not os.path.exists(default_html_file):
        print(f"❌ Test HTML file not found: {default_html_file}")
        print("Please make sure the HTML file exists in the utils directory.")
        return

    tester = LighthouseParserTester()
    ok = tester.run_full_test(default_html_file)
    if ok:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        print("\nTroubleshooting tips:")
        print("1) Ensure Lighthouse service is running: cd ../lighthouse-service && node server.js")
        print("2) Check port 3001 is free")
        print("3) Verify the HTML file exists and is readable")


if __name__ == "__main__":
    main()
