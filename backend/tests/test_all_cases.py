#!/usr/bin/env python3
"""
Test All SEO Cases
Run the full pipeline on all 8 test files and generate comprehensive reports.
"""

import os
import sys
import json
import html
from pathlib import Path
import time

script_path = Path(__file__).resolve()
project_root = script_path.parent.parent
sys.path.insert(0, str(project_root))

print(f"DEBUG: script file: {__file__}")
print(f"DEBUG: project root: {project_root}")

try:
    from app.services.seo_analysis_service import SEOAnalysisService
    from app.core.lhr_parser import LHRTool
    from app.core.matcher import match_issues
    from app.core.issue_merger import transform_to_simple_issues_with_insertions
    from app.core.llm_tool import LLMTool
    from app.core.html_editor import HTMLEditor
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def save_json_file(data, filename, description, case_name=""):
    """Save a Python object as JSON file."""
    output_dir = Path(__file__).parent / "pipeline_outputs" / case_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ {description} saved to: {filepath}")
    return filepath

def test_single_case(case_file):
    """Test a single case file."""
    case_name = case_file.stem
    print(f"\n{'='*60}")
    print(f"🧪 Testing Case: {case_name}")
    print(f"{'='*60}")
    
    # Read the test HTML file
    print(f"📖 Reading test HTML file: {case_file}")
    with open(case_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"✅ HTML loaded, length: {len(html_content)} chars")
    
    # Step 1: Call Lighthouse service
    print(f"\n🔍 Step 1: Call Lighthouse service for {case_name}...")
    
    max_retries = 3
    lighthouse_result = None
    seo_score = 0
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Lighthouse attempt {attempt}/{max_retries}...")
            seo_service = SEOAnalysisService()
            lighthouse_result = seo_service._call_lighthouse_service(html_content)
            
            seo_score = lighthouse_result.get('seoScore', 0)
            print(f"📊 Lighthouse attempt {attempt} - SEO score: {seo_score}")
            
            if seo_score > 0:
                print(f"✅ Lighthouse call successful! SEO score: {seo_score}")
                break
            else:
                print(f"⚠️  Lighthouse attempt {attempt} returned SEO score 0, retrying...")
                if attempt < max_retries:
                    time.sleep(2)
                else:
                    print(f"❌ All {max_retries} Lighthouse attempts failed with SEO score 0")
                    return None
                    
        except Exception as e:
            print(f"❌ Lighthouse attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                print(f"❌ All {max_retries} Lighthouse attempts failed")
                return None
    
    # Save Lighthouse result
    save_json_file(
        lighthouse_result, 
        "01_lighthouse_raw.json", 
        "Lighthouse raw result",
        case_name
    )
    
    # Step 2: Run LHR parser
    print(f"\n📊 Step 2: Run LHR parser for {case_name}...")
    try:
        parser = LHRTool()
        parsed_result = parser.parse_lhr_json(lighthouse_result)
        
        save_json_file(
            parsed_result, 
            "02_parser_output.json", 
            "LHR parser output",
            case_name
        )
        
        print(f"✅ Parser OK, issues: {len(parsed_result.get('issues', []))}")
        
    except Exception as e:
        print(f"❌ Parser failed: {e}")
        return None
    
    # Step 3: Run matcher
    print(f"\n🎯 Step 3: Run matcher for {case_name}...")
    try:
        matched_result = match_issues(html_content, parsed_result)
        
        save_json_file(
            matched_result, 
            "03_matcher_output.json", 
            "Matcher output",
            case_name
        )
        
        print(f"✅ Matcher OK, matched issues: {len(matched_result.get('issues', []))}")
        
    except Exception as e:
        print(f"❌ Matcher failed: {e}")
        return None
    
    # Step 4: Run merger
    print(f"\n🔗 Step 4: Run merger for {case_name}...")
    try:
        merged_result = transform_to_simple_issues_with_insertions(matched_result)
        
        save_json_file(
            merged_result, 
            "04_merger_output.json", 
            "Merger output",
            case_name
        )
        
        print(f"✅ Merger OK, merged issues: {len(merged_result)}")
        
    except Exception as e:
        print(f"❌ Merger failed: {e}")
        return None
    
    # Step 5: Run LLM optimization
    print(f"\n🤖 Step 5: Run LLM optimization for {case_name}...")
    try:
        llm_tool = LLMTool()
        optimized_result = llm_tool.get_batch_modification(merged_result)
        
        save_json_file(
            optimized_result, 
            "05_llm_output.json", 
            "LLM output",
            case_name
        )
        
        print(f"✅ LLM OK, optimized issues: {len(optimized_result.get('issues', []))}")
        
    except Exception as e:
        print(f"❌ LLM failed: {e}")
        return None
    
    # Step 6: Apply HTML edits
    print(f"\n✏️  Step 6: Apply HTML edits for {case_name}...")
    try:
        html_editor = HTMLEditor()
        optimized_html = html_editor.apply_optimizations(html_content, optimized_result)
        
        # Save optimized HTML
        output_dir = Path(__file__).parent / "pipeline_outputs" / case_name
        optimized_html_path = output_dir / "08_optimized_html.html"
        with open(optimized_html_path, 'w', encoding='utf-8') as f:
            f.write(optimized_html)
        
        print(f"✅ HTML editor OK, optimized HTML saved to: {optimized_html_path}")
        
    except Exception as e:
        print(f"❌ HTML editor failed: {e}")
        return None
    
    # Step 7: Re-run Lighthouse on optimized HTML
    print(f"\n🔍 Step 7: Re-run Lighthouse on optimized HTML for {case_name}...")
    
    optimized_lighthouse_result = None
    optimized_seo_score = 0
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Optimized Lighthouse attempt {attempt}/{max_retries}...")
            seo_service = SEOAnalysisService()
            optimized_lighthouse_result = seo_service._call_lighthouse_service(optimized_html)
            
            optimized_seo_score = optimized_lighthouse_result.get('seoScore', 0)
            print(f"📊 Optimized Lighthouse attempt {attempt} - SEO score: {optimized_seo_score}")
            
            if optimized_seo_score > 0:
                print(f"✅ Optimized Lighthouse call successful! SEO score: {optimized_seo_score}")
                break
            else:
                print(f"⚠️  Optimized Lighthouse attempt {attempt} returned SEO score 0, retrying...")
                if attempt < max_retries:
                    time.sleep(2)
                else:
                    print(f"❌ All {max_retries} optimized Lighthouse attempts failed")
                    return None
                    
        except Exception as e:
            print(f"❌ Optimized Lighthouse attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                print(f"❌ All {max_retries} optimized Lighthouse attempts failed")
                return None
    
    # Save optimized Lighthouse result
    save_json_file(
        optimized_lighthouse_result, 
        "11_lighthouse_optimized.json", 
        "Optimized Lighthouse result",
        case_name
    )
    
    # Calculate improvement
    improvement = optimized_seo_score - seo_score
    improvement_percentage = (improvement / seo_score * 100) if seo_score > 0 else 0
    
    # Save summary
    summary = {
        "case_name": case_name,
        "original_seo_score": seo_score,
        "optimized_seo_score": optimized_seo_score,
        "improvement": improvement,
        "improvement_percentage": improvement_percentage,
        "issues_detected": len(parsed_result.get('issues', [])),
        "issues_matched": len(matched_result.get('issues', [])),
        "issues_optimized": len(optimized_result.get('issues', []))
    }
    
    save_json_file(
        summary, 
        "09_case_summary.json", 
        "Case summary",
        case_name
    )
    
    print(f"\n📊 Case {case_name} Results:")
    print(f"   Original SEO Score: {seo_score}")
    print(f"   Optimized SEO Score: {optimized_seo_score}")
    print(f"   Improvement: {improvement} points ({improvement_percentage:.1f}%)")
    print(f"   Issues Detected: {summary['issues_detected']}")
    print(f"   Issues Matched: {summary['issues_matched']}")
    print(f"   Issues Optimized: {summary['issues_optimized']}")
    
    return summary

def test_all_cases():
    """Test all 8 cases and generate comprehensive report."""
    print("🚀 Starting comprehensive SEO test on all 8 cases...")
    
    # Get all test case files
    test_cases_dir = Path(__file__).parent / "test_cases"
    test_files = sorted(test_cases_dir.glob("*.html"))
    
    if not test_files:
        print(f"❌ No test files found in {test_cases_dir}")
        return
    
    print(f"📁 Found {len(test_files)} test files:")
    for file in test_files:
        print(f"   - {file.name}")
    
    # Test each case
    all_results = []
    
    for test_file in test_files:
        result = test_single_case(test_file)
        if result:
            all_results.append(result)
        else:
            print(f"❌ Failed to test {test_file.name}")
        
        # Add delay between tests
        print(f"⏳ Waiting 5 seconds before next test...")
        time.sleep(5)
    
    # Generate comprehensive report
    print(f"\n{'='*60}")
    print(f"📊 COMPREHENSIVE TEST REPORT")
    print(f"{'='*60}")
    
    if all_results:
        # Calculate overall statistics
        total_improvement = sum(r['improvement'] for r in all_results)
        avg_improvement = total_improvement / len(all_results)
        successful_cases = len(all_results)
        
        print(f"✅ Successfully tested {successful_cases}/{len(test_files)} cases")
        print(f"📈 Total improvement across all cases: {total_improvement:.1f} points")
        print(f"📊 Average improvement per case: {avg_improvement:.1f} points")
        
        print(f"\n📋 Detailed Results:")
        print(f"{'Case Name':<25} {'Original':<10} {'Optimized':<10} {'Improvement':<12} {'%':<8}")
        print(f"{'-'*70}")
        
        for result in all_results:
            print(f"{result['case_name']:<25} {result['original_seo_score']:<10.1f} {result['optimized_seo_score']:<10.1f} {result['improvement']:<12.1f} {result['improvement_percentage']:<8.1f}%")
        
        # Save comprehensive report
        comprehensive_report = {
            "test_summary": {
                "total_cases": len(test_files),
                "successful_cases": successful_cases,
                "total_improvement": total_improvement,
                "average_improvement": avg_improvement
            },
            "individual_results": all_results
        }
        
        output_dir = Path(__file__).parent / "pipeline_outputs"
        report_path = output_dir / "comprehensive_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comprehensive report saved to: {report_path}")
        
    else:
        print("❌ No cases were successfully tested")

if __name__ == "__main__":
    test_all_cases()
