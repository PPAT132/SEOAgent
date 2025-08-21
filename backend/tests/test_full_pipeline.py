#!/usr/bin/env python3
"""
Test Full SEO Analysis Pipeline
Step-by-step test of each component, writing intermediate outputs to files.
"""

import os
import sys
import json
import html
from pathlib import Path

script_path = Path(__file__).resolve()
project_root = script_path.parent.parent
sys.path.insert(0, str(project_root))

print(f"DEBUG: script file: {__file__}")
print(f"DEBUG: project root: {project_root}")
print(f"DEBUG: sys.path: {sys.path}")

try:
    from app.services.seo_analysis_service import SEOAnalysisService
    from app.core.lhr_parser import LHRTool
    from app.core.matcher import match_issues
    from app.core.issue_merger import transform_to_simple_issues_with_insertions
    from app.core.llm_tool import LLMTool
    from app.core.html_editor import HTMLEditor
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"CWD: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    print(f"project_root: {project_root}")
    sys.exit(1)

def save_json_file(data, filename, description):
    """Save a Python object as JSON file."""
    output_dir = Path(__file__).parent / "pipeline_outputs"
    output_dir.mkdir(exist_ok=True)
    
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ {description} saved to: {filepath}")
    return filepath

def test_full_pipeline():
    """Run the full SEO analysis pipeline."""
    
    # 1. Read test HTML file
    print("📖 Reading test HTML file...")
    # html_file_path = Path(__file__).parent / "test_cases" / "03_meta_description_missing.html"
    html_file_path = Path(__file__).parent / "test_cases" / "01_image_alt_missing.html"
    
    if not html_file_path.exists():
        print(f"❌ HTML file not found: {html_file_path}")
        return
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"✅ HTML loaded, length: {len(html_content)} chars")
    
    # 2. Call Lighthouse service with retry logic
    print("\n🔍 Step 1: call Lighthouse service...")
    
    max_retries = 5
    lighthouse_result = None
    seo_score = 0
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Lighthouse attempt {attempt}/{max_retries}...")
            seo_service = SEOAnalysisService()
            lighthouse_result = seo_service._call_lighthouse_service(html_content)
            
            # Check if we got a valid SEO score
            seo_score = lighthouse_result.get('seoScore', 0)
            print(f"📊 Lighthouse attempt {attempt} - SEO score: {seo_score}")
            
            # If we got a valid score (not 0), break out of retry loop
            if seo_score > 0:
                print(f"✅ Lighthouse call successful! SEO score: {seo_score}")
                break
            else:
                print(f"⚠️  Lighthouse attempt {attempt} returned SEO score 0, retrying...")
                if attempt < max_retries:
                    print(f"⏳ Waiting 3 seconds before retry...")
                    import time
                    time.sleep(3)
                else:
                    print(f"❌ All {max_retries} Lighthouse attempts failed with SEO score 0")
                    print(f"❌ Pipeline failed - cannot proceed with LLM optimization")
                    return
                    
        except Exception as e:
            print(f"❌ Lighthouse attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(f"⏳ Waiting 3 seconds before retry...")
                import time
                time.sleep(3)
            else:
                print(f"❌ All {max_retries} Lighthouse attempts failed")
                return
    
    # Save the successful Lighthouse result
    save_json_file(
        lighthouse_result, 
        "01_lighthouse_raw.json", 
        "Lighthouse raw result"
    )
    
    print(f"✅ Lighthouse service completed successfully with SEO score: {seo_score}")
    
    # 3. Run LHR parser
    print("\n📊 Step 2: run LHR parser...")
    try:
        parser = LHRTool()
        parsed_result = parser.parse_lhr_json(lighthouse_result)
        
        # Save parsed result
        save_json_file(
            parsed_result, 
            "02_parser_output.json", 
            "LHR parser output"
        )
        
        print(f"✅ Parser OK, issues: {len(parsed_result.get('issues', []))}")
        
    except Exception as e:
        print(f"❌ Parser failed: {e}")
        return
    
    # 4. Run matcher
    print("\n🎯 Step 3: run matcher...")
    try:
        matched_result = match_issues(html_content, parsed_result)
        
        # Save matching result
        save_json_file(
            matched_result, 
            "04_matcher_output.json", 
            "Matcher output"
        )
        
        matched_issues = matched_result.get('issues', [])
        matched_count = len([i for i in matched_issues if i.get('match_status') == 'matched'])
        print(f"✅ Matcher OK, total issues: {len(matched_issues)}, matched: {matched_count}")
        
    except Exception as e:
        print(f"❌ Matcher failed: {e}")
        return
    
    # 5. Run issue merger
    print("\n🔧 Step 4: run issue merger...")
    try:
        merged_issues = transform_to_simple_issues_with_insertions(matched_result)
        
        # Save merged result
        save_json_file(
            merged_issues, 
            "04_merger_output.json", 
            "Issue merger output"
        )
        
        print(f"✅ Merger OK, merged issues: {len(merged_issues)}")
        
    except Exception as e:
        print(f"❌ Merger failed: {e}")
        return
    
    # 6. Build final result
    print("\n📝 Step 5: build final result...")
    try:
        final_result = seo_service._build_final_result(
            parsed_result, 
            merged_issues, 
            html_content
        )
        temp_result = final_result
        
        # Save final result
        if hasattr(final_result, 'dict'):
            final_dict = final_result.dict()
        else:
            final_dict = final_result.__dict__
        
        save_json_file(
            final_dict, 
            "05_final_result.json", 
            "Final SEO analysis result"
        )
        
        print(f"✅ Final result OK, SEO score: {final_dict.get('seo_score', 'N/A')}")

    except Exception as e:
        print(f"❌ Final result failed: {e}")
        return
    
    # 7. call LLM
    print("\n🤖 Step 6: calling LLM...")
    try:
        agent = LLMTool()

        optimized_res = agent.get_batch_modification(temp_result)

        if hasattr(optimized_res, 'dict'):
            optimized_res = optimized_res.dict()
        else:
            optimized_res = optimized_res.__dict__
        
        save_json_file(
            optimized_res,
            "06_optimized_result.json",
            "LLM optimized Result"
        )
        
        print(f"✅ LLM optimization OK, processed {len(optimized_res.get('issues', []))} issues")
        
    except Exception as e:
        print(f"❌ LLM optimization failed: {e}")
        return
    
    # 8. Apply HTML edits
    print("\n✏️  Step 7: applying HTML edits...")
    try:
        # Convert back to SEOAnalysisResult for the editor
        from app.schemas.seo_analysis import SEOAnalysisResult, IssueInfo
        
        # Reconstruct the SEOAnalysisResult from the optimized JSON
        issues = []
        for issue_data in optimized_res.get('issues', []):
            issue = IssueInfo(
                title=issue_data.get('title', ''),
                start_line=issue_data.get('start_line', 1),
                end_line=issue_data.get('end_line', 1),
                raw_html=issue_data.get('raw_html', ''),
                optimized_html=issue_data.get('optimized_html', '')
            )
            issues.append(issue)
        
        seo_result = SEOAnalysisResult(
            seo_score=optimized_res.get('seo_score', 0.0),
            total_lines=optimized_res.get('total_lines', len(html_content.split('\n'))),
            issues=issues,
            context=""
        )
        
        # Sort issues in descending order by end_line (as expected by the editor)
        seo_result.issues.sort(key=lambda x: x.end_line, reverse=True)
        
        # Initialize the HTML editor
        editor = HTMLEditor()
        
        # Apply the fixes
        optimized_html = editor.modify_html(html_content, seo_result)
        
        # Save the original HTML for comparison
        original_output_path = Path(__file__).parent / "pipeline_outputs" / "07_original_html.html"
        with open(original_output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Original HTML saved: 07_original_html.html")
        
        # Save the optimized HTML
        optimized_output_path = Path(__file__).parent / "pipeline_outputs" / "08_optimized_html.html"
        with open(optimized_output_path, 'w', encoding='utf-8') as f:
            f.write(optimized_html)
        print(f"✅ Optimized HTML saved: 08_optimized_html.html")
        
        # Create a summary report
        report_path = Path(__file__).parent / "pipeline_outputs" / "09_pipeline_summary.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Full SEO Pipeline Summary Report\n")
            f.write("================================\n\n")
            f.write(f"Pipeline executed: {__file__}\n")
            f.write(f"HTML file: test_seo_page.html\n")
            original_lines = len(html_content.split('\n'))
            f.write(f"Original HTML lines: {original_lines}\n")
            f.write(f"SEO Score: {seo_result.seo_score}\n")
            f.write(f"Issues processed: {len(seo_result.issues)}\n")
            f.write(f"Original size: {len(html_content)} characters\n")
            f.write(f"Optimized size: {len(optimized_html)} characters\n\n")
            
            f.write("Issues processed:\n")
            f.write("-" * 80 + "\n")
            for i, issue in enumerate(seo_result.issues, 1):
                f.write(f"{i}. {issue.title}\n")
                f.write(f"   Lines {issue.start_line}-{issue.end_line}\n")
                f.write(f"   Raw: {issue.raw_html[:100]}{'...' if len(issue.raw_html) > 100 else ''}\n")
                f.write(f"   Fixed: {issue.optimized_html[:100]}{'...' if len(issue.optimized_html) > 100 else ''}\n\n")
        
        print(f"✅ Pipeline summary saved: 09_pipeline_summary.txt")
        print(f"✅ HTML editing completed successfully!")
        
        # 9. Analyze optimization results and compare scores
        print("\n📊 Step 8: analyzing optimization results...")
        try:
            # Run Lighthouse on the optimized HTML to get new score
            print("🔄 Running Lighthouse on optimized HTML...")
            optimized_seo_service = SEOAnalysisService()
            optimized_lighthouse_result = optimized_seo_service._call_lighthouse_service(optimized_html)
            optimized_seo_score = optimized_lighthouse_result.get('seoScore', 0)
            
            # Save the optimized Lighthouse result
            save_json_file(
                optimized_lighthouse_result, 
                "11_lighthouse_optimized.json", 
                "Lighthouse result after optimization"
            )
            
            print(f"📊 Original SEO Score: {seo_score}")
            print(f"📊 Optimized SEO Score: {optimized_seo_score}")
            print(f"📈 Score Improvement: {optimized_seo_score - seo_score} points")
            
            # Create optimization summary report
            optimization_report_path = Path(__file__).parent / "pipeline_outputs" / "10_optimization_summary.html"
            
            # Calculate improvement percentage
            improvement_percentage = ((optimized_seo_score - seo_score) / seo_score * 100) if seo_score > 0 else 0
            
            # Generate HTML content
            html_content_report = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>SEO Optimization Results Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .score-comparison {{ display: flex; justify-content: space-around; margin: 30px 0; }}
        .score-box {{ text-align: center; padding: 20px; border-radius: 8px; }}
        .original {{ background: #ffebee; border: 2px solid #f44336; }}
        .optimized {{ background: #e8f5e8; border: 2px solid #4caf50; }}
        .score {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
        .original .score {{ color: #f44336; }}
        .optimized .score {{ color: #4caf50; }}
        .improvement {{ text-align: center; margin: 20px 0; padding: 20px; background: #e3f2fd; border-radius: 8px; }}
        .improvement h2 {{ color: #1976d2; margin: 0 0 10px 0; }}
        .issues-section {{ margin: 30px 0; }}
        .issue {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #2196f3; border-radius: 4px; }}
        .issue h3 {{ margin: 0 0 10px 0; color: #1976d2; }}
        .before-after {{ display: flex; gap: 20px; }}
        .before, .after {{ flex: 1; }}
        .before h4 {{ color: #f44336; }}
        .after h4 {{ color: #4caf50; }}
        pre {{ background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; }}
        .stats {{ background: #f0f8ff; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .stats h3 {{ margin: 0 0 15px 0; color: #1976d2; }}
        .stat-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 5px 0; border-bottom: 1px solid #e0e0e0; }}
        .lighthouse-details {{ background: #fff3e0; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9800; }}
        .lighthouse-details h3 {{ color: #f57c00; margin: 0 0 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 SEO Optimization Results Summary</h1>
        
        <div class="score-comparison">
            <div class="score-box original">
                <h2>Before Optimization</h2>
                <div class="score">{seo_score}</div>
                <p>Original SEO Score</p>
            </div>
            <div class="score-box optimized">
                <h2>After Optimization</h2>
                <div class="score">{optimized_seo_score}</div>
                <p>Optimized SEO Score</p>
            </div>
        </div>
        
        <div class="improvement">
            <h2>📈 Overall Improvement</h2>
            <p><strong>Score Increase:</strong> {optimized_seo_score - seo_score} points</p>
            <p><strong>Percentage Improvement:</strong> {improvement_percentage:.1f}%</p>
        </div>
        
        <div class="lighthouse-details">
            <h3>🔍 Lighthouse Analysis Details</h3>
            <div class="stat-row">
                <span>Original Lighthouse Analysis:</span>
                <span><strong>Completed ✅</strong></span>
            </div>
            <div class="stat-row">
                <span>Original SEO Score:</span>
                <span><strong>{seo_score} points</strong></span>
            </div>
            <div class="stat-row">
                <span>Optimized Lighthouse Analysis:</span>
                <span><strong>Completed ✅</strong></span>
            </div>
            <div class="stat-row">
                <span>Optimized SEO Score:</span>
                <span><strong>{optimized_seo_score} points</strong></span>
            </div>
            <div class="stat-row">
                <span>Analysis Method:</span>
                <span><strong>Automated Pipeline with Re-analysis</strong></span>
            </div>
            <div class="stat-row">
                <span>Total Lighthouse Runs:</span>
                <span><strong>2 (Before + After)</strong></span>
            </div>
        </div>
        
        <div class="stats">
            <h3>📊 Optimization Statistics</h3>
            <div class="stat-row">
                <span>Total Issues Processed:</span>
                <span><strong>{len(seo_result.issues)}</strong></span>
            </div>
            <div class="stat-row">
                <span>Original HTML Size:</span>
                <span><strong>{len(html_content):,} characters</strong></span>
            </div>
            <div class="stat-row">
                <span>Optimized HTML Size:</span>
                <span><strong>{len(optimized_html):,} characters</strong></span>
            </div>
            <div class="stat-row">
                <span>Size Change:</span>
                <span><strong>{len(optimized_html) - len(html_content):+,} characters</strong></span>
            </div>
        </div>
        
        <div class="issues-section">
            <h3>🔧 Issues Fixed</h3>"""
            
            # Add each issue with before/after comparison
            for i, issue in enumerate(seo_result.issues, 1):
                html_content_report += f"""
            <div class="issue">
                <h3>Issue {i}: {html.escape(issue.title)}</h3>
                <div class="before-after">
                    <div class="before">
                        <h4>❌ Before (Lines {issue.start_line}-{issue.end_line})</h4>
                        <pre>{html.escape(issue.raw_html[:300] + ("..." if len(issue.raw_html) > 300 else ""))}</pre>
                    </div>
                    <div class="after">
                        <h4>✅ After</h4>
                        <pre>{html.escape(issue.optimized_html[:300] + ("..." if len(issue.optimized_html) > 300 else ""))}</pre>
                    </div>
                </div>
            </div>"""
                
            html_content_report += f"""
        </div>
        
        <div class="stats">
            <h3>📁 Generated Files</h3>
            <div class="stat-row">
                <span>Original HTML:</span>
                <span><a href="07_original_html.html">07_original_html.html</a></span>
            </div>
            <div class="stat-row">
                <span>Optimized HTML:</span>
                <span><a href="08_optimized_html.html">08_optimized_html.html</a></span>
            </div>
            <div class="stat-row">
                <span>Pipeline Summary:</span>
                <span><a href="09_pipeline_summary.txt">09_pipeline_summary.txt</a></span>
            </div>
            <div class="stat-row">
                <span>Original Lighthouse Report:</span>
                <span><a href="01_lighthouse_raw.json">01_lighthouse_raw.json</a></span>
            </div>
            <div class="stat-row">
                <span>Optimized Lighthouse Report:</span>
                <span><a href="11_lighthouse_optimized.json">11_lighthouse_optimized.json</a></span>
            </div>
        </div>
    </div>
</body>
</html>"""
            
            # Write the HTML file
            with open(optimization_report_path, 'w', encoding='utf-8') as f:
                f.write(html_content_report)
            
            print(f"✅ Optimization summary saved: 10_optimization_summary.html")
            print(f"📊 Final Results:")
            print(f"   Original Score: {seo_score}")
            print(f"   Optimized Score: {optimized_seo_score}")
            print(f"   Improvement: {optimized_seo_score - seo_score} points")
            
            # Also save to pipeline summary for easy access
            summary_path = Path(__file__).parent / "pipeline_outputs" / "09_pipeline_summary.txt"
            with open(summary_path, 'a', encoding='utf-8') as f:
                f.write(f"\n\n=== OPTIMIZATION RESULTS ===\n")
                f.write(f"Original SEO Score: {seo_score}\n")
                f.write(f"Optimized SEO Score: {optimized_seo_score}\n")
                f.write(f"Score Improvement: {optimized_seo_score - seo_score} points\n")
                f.write(f"Percentage Improvement: {improvement_percentage:.1f}%\n")
            
        except Exception as e:
            print(f"⚠️  Could not analyze optimization results: {e}")
        
    except Exception as e:
        print(f"❌ HTML editing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 9. Re-analyze optimized HTML to compare issue counts
    print("\n🔄 Step 9: Re-analyzing optimized HTML to compare issue counts...")
    try:
        # Read the optimized HTML
        optimized_html_path = Path(__file__).parent / "pipeline_outputs" / "08_optimized_html.html"
        with open(optimized_html_path, 'r', encoding='utf-8') as f:
            optimized_html_content = f.read()
        
        print(f"✅ Loaded optimized HTML, length: {len(optimized_html_content)} chars")
        
        # Run Lighthouse on optimized HTML with retry logic
        print("🔍 Running Lighthouse on optimized HTML...")
        max_retries = 3
        optimized_lighthouse_result = None
        optimized_seo_score = 0
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔄 Lighthouse attempt {attempt}/{max_retries} for optimized HTML...")
                optimized_seo_service = SEOAnalysisService()
                optimized_lighthouse_result = optimized_seo_service._call_lighthouse_service(optimized_html_content)
                optimized_seo_score = optimized_lighthouse_result.get('seoScore', 0)
                print(f"✅ Lighthouse call successful for optimized HTML! SEO score: {optimized_seo_score}")
                break
            except Exception as e:
                print(f"❌ Lighthouse attempt {attempt} failed for optimized HTML: {e}")
                if attempt < max_retries:
                    print(f"⏳ Waiting 3 seconds before retry...")
                    import time
                    time.sleep(3)
                else:
                    print(f"❌ All {max_retries} Lighthouse attempts failed for optimized HTML")
                    raise Exception(f"Lighthouse service call failed for optimized HTML after {max_retries} attempts: {e}")
        
        # Save optimized Lighthouse result
        save_json_file(
            optimized_lighthouse_result, 
            "12_lighthouse_optimized_raw.json", 
            "Lighthouse raw result for optimized HTML"
        )
        
        print(f"✅ Lighthouse on optimized HTML completed, SEO score: {optimized_seo_score}")
        
        # Run LHR parser on optimized result
        print("📊 Running LHR parser on optimized result...")
        optimized_parser = LHRTool()
        optimized_parsed_result = optimized_parser.parse_lhr_json(optimized_lighthouse_result)
        
        # Save optimized parsed result
        save_json_file(
            optimized_parsed_result, 
            "13_parser_optimized_output.json", 
            "LHR parser output for optimized HTML"
        )
        
        optimized_issues_count = len(optimized_parsed_result.get('issues', []))
        print(f"✅ Parser OK for optimized HTML, issues: {optimized_issues_count}")
        
        # Run matcher on optimized result
        print("🎯 Running matcher on optimized result...")
        optimized_matched_result = match_issues(optimized_html_content, optimized_parsed_result)
        
        # Save optimized matching result
        save_json_file(
            optimized_matched_result, 
            "14_matcher_optimized_output.json", 
            "Matcher output for optimized HTML"
        )
        
        optimized_matched_issues = optimized_matched_result.get('issues', [])
        optimized_matched_count = len([i for i in optimized_matched_issues if i.get('match_status') == 'matched'])
        print(f"✅ Matcher OK for optimized HTML, total issues: {len(optimized_matched_issues)}, matched: {optimized_matched_count}")
        
        # Run issue merger on optimized result
        print("🔧 Running issue merger on optimized result...")
        optimized_merged_issues = transform_to_simple_issues_with_insertions(optimized_matched_result)
        
        # Save optimized merged result
        save_json_file(
            optimized_merged_issues, 
            "15_merger_optimized_output.json", 
            "Issue merger output for optimized HTML"
        )
        
        print(f"✅ Merger OK for optimized HTML, merged issues: {len(optimized_merged_issues)}")
        
        # Compare issue counts
        original_issues = len(parsed_result.get('issues', []))
        original_matched = len([i for i in matched_result.get('issues', []) if i.get('match_status') == 'matched'])
        original_merged = len(merged_issues)
        
        print(f"\n📊 ISSUE COUNT COMPARISON:")
        print(f"   Original HTML:")
        print(f"     - Parsed issues: {original_issues}")
        print(f"     - Matched issues: {original_matched}")
        print(f"     - Merged issues: {original_merged}")
        print(f"   Optimized HTML:")
        print(f"     - Parsed issues: {optimized_issues_count}")
        print(f"     - Matched issues: {optimized_matched_count}")
        print(f"     - Merged issues: {len(optimized_merged_issues)}")
        print(f"   Improvements:")
        print(f"     - Parsed issues reduced: {original_issues - optimized_issues_count}")
        print(f"     - Matched issues reduced: {original_matched - optimized_matched_count}")
        print(f"     - Merged issues reduced: {original_merged - len(optimized_merged_issues)}")
        
        # Create comparison summary
        comparison_path = Path(__file__).parent / "pipeline_outputs" / "16_issue_comparison_summary.txt"
        with open(comparison_path, 'w', encoding='utf-8') as f:
            f.write("Issue Count Comparison Summary\n")
            f.write("==============================\n\n")
            f.write(f"Analysis Date: {__file__}\n")
            f.write(f"Original HTML File: test_cases/03_meta_description_missing.html\n")
            f.write(f"Optimized HTML File: 08_optimized_html.html\n\n")
            
            f.write("ORIGINAL HTML ANALYSIS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"SEO Score: {seo_score}\n")
            f.write(f"Parsed Issues: {original_issues}\n")
            f.write(f"Matched Issues: {original_matched}\n")
            f.write(f"Merged Issues: {original_merged}\n\n")
            
            f.write("OPTIMIZED HTML ANALYSIS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"SEO Score: {optimized_seo_score}\n")
            f.write(f"Parsed Issues: {optimized_issues_count}\n")
            f.write(f"Matched Issues: {optimized_matched_count}\n")
            f.write(f"Merged Issues: {len(optimized_merged_issues)}\n\n")
            
            f.write("IMPROVEMENTS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"SEO Score Improvement: {optimized_seo_score - seo_score} points\n")
            f.write(f"Parsed Issues Reduced: {original_issues - optimized_issues_count}\n")
            f.write(f"Matched Issues Reduced: {original_matched - optimized_matched_count}\n")
            f.write(f"Merged Issues Reduced: {original_merged - len(optimized_merged_issues)}\n")
            f.write(f"Percentage Reduction (Parsed): {((original_issues - optimized_issues_count) / original_issues * 100):.1f}%\n")
            f.write(f"Percentage Reduction (Matched): {((original_matched - optimized_matched_count) / original_matched * 100):.1f}%\n")
            f.write(f"Percentage Reduction (Merged): {((original_merged - len(optimized_merged_issues)) / original_merged * 100):.1f}%\n\n")
            
            f.write("FILES GENERATED:\n")
            f.write("-" * 40 + "\n")
            f.write("Original Analysis:\n")
            f.write("  01_lighthouse_raw.json\n")
            f.write("  02_parser_output.json\n")
            f.write("  04_matcher_output.json\n")
            f.write("  04_merger_output.json\n\n")
            f.write("Optimized Analysis:\n")
            f.write("  12_lighthouse_optimized_raw.json\n")
            f.write("  13_parser_optimized_output.json\n")
            f.write("  14_matcher_optimized_output.json\n")
            f.write("  15_merger_optimized_output.json\n")
            f.write("  16_issue_comparison_summary.txt\n")
        
        print(f"✅ Issue comparison summary saved: 16_issue_comparison_summary.txt")
        
    except Exception as e:
        print(f"❌ Re-analysis of optimized HTML failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Full pipeline completed!")
    print("📁 Outputs saved under tests/pipeline_outputs/")
    print("\n📋 Files:")
    print("  01_lighthouse_raw.json              - Lighthouse raw result")
    print("  02_parser_output.json               - LHR parser output")
    print("  04_matcher_output.json              - Matcher output")
    print("  04_merger_output.json               - Issue merger output")
    print("  05_final_result.json                - Final SEO analysis result")
    print("  06_optimized_result.json            - LLM optimized result")
    print("  07_original_html.html               - Original HTML file")
    print("  08_optimized_html.html              - Final optimized HTML file")
    print("  09_pipeline_summary.txt             - Complete pipeline summary")
    print("  10_optimization_summary.html        - Optimization summary")
    print("  11_lighthouse_optimized.json        - Lighthouse result after optimization")
    print("  12_lighthouse_optimized_raw.json    - Lighthouse raw result for optimized HTML")
    print("  13_parser_optimized_output.json     - LHR parser output for optimized HTML")
    print("  14_matcher_optimized_output.json    - Matcher output for optimized HTML")
    print("  15_merger_optimized_output.json     - Issue merger output for optimized HTML")
    print("  16_issue_comparison_summary.txt     - Issue count comparison summary")

if __name__ == "__main__":
    test_full_pipeline()
