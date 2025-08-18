#!/usr/bin/env python3
"""
Test Full SEO Analysis Pipeline
Step-by-step test of each component, writing intermediate outputs to files.
"""

import os
import sys
import json
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
    
    # 1. 读取测试HTML文件
    print("📖 Reading test HTML file...")
    html_file_path = Path(__file__).parent / "test_seo_page.html"
    
    if not html_file_path.exists():
        print(f"❌ HTML file not found: {html_file_path}")
        return
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"✅ HTML loaded, length: {len(html_content)} chars")
    
    # 2. 调用Lighthouse服务
    print("\n🔍 Step 1: call Lighthouse service...")
    try:
        seo_service = SEOAnalysisService()
        lighthouse_result = seo_service._call_lighthouse_service(html_content)
        
        save_json_file(
            lighthouse_result, 
            "01_lighthouse_raw.json", 
            "Lighthouse raw result"
        )
        
        print(f"✅ Lighthouse call OK, SEO score: {lighthouse_result.get('seoScore', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Lighthouse call failed: {e}")
        return
    
    # 3. 运行LHR解析器
    print("\n📊 Step 2: run LHR parser...")
    try:
        parser = LHRTool()
        parsed_result = parser.parse_lhr_json(lighthouse_result)
        
        # 保存解析后的结果
        save_json_file(
            parsed_result, 
            "02_parser_output.json", 
            "LHR parser output"
        )
        
        print(f"✅ Parser OK, issues: {len(parsed_result.get('issues', []))}")
        
    except Exception as e:
        print(f"❌ Parser failed: {e}")
        return
    
    # 4. 运行匹配器
    print("\n🎯 Step 3: run matcher...")
    try:
        matched_result = match_issues(html_content, parsed_result)
        
        # 保存匹配结果
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
    
    # 5. 运行问题合并器
    print("\n🔧 Step 4: run issue merger...")
    try:
        merged_issues = transform_to_simple_issues_with_insertions(matched_result)
        
        # 保存合并结果
        save_json_file(
            merged_issues, 
            "04_merger_output.json", 
            "Issue merger output"
        )
        
        print(f"✅ Merger OK, merged issues: {len(merged_issues)}")
        
    except Exception as e:
        print(f"❌ Merger failed: {e}")
        return
    
    # 6. 构建最终结果
    print("\n📝 Step 5: build final result...")
    try:
        final_result = seo_service._build_final_result(
            parsed_result, 
            merged_issues, 
            html_content
        )
        
        # 保存最终结果
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
    
    print("\n🎉 Full pipeline completed!")
    print("📁 Outputs saved under tests/pipeline_outputs/")
    print("\n📋 Files:")
    print("  01_lighthouse_raw.json      - Lighthouse raw result")
    print("  02_parser_output.json       - LHR parser output")
    print("  03_matcher_output.json      - Matcher output")
    print("  04_merger_output.json       - Issue merger output")
    print("  05_final_result.json        - Final SEO analysis result")

if __name__ == "__main__":
    test_full_pipeline()
