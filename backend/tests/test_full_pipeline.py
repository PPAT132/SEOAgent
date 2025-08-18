#!/usr/bin/env python3
"""
Test Full SEO Analysis Pipeline
逐步测试每个组件，生成中间结果文件
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent
sys.path.insert(0, str(project_root))

print(f"DEBUG: 脚本路径: {__file__}")
print(f"DEBUG: 项目根目录: {project_root}")
print(f"DEBUG: Python路径: {sys.path}")

try:
    from app.services.seo_analysis_service import SEOAnalysisService
    from app.core.lhr_parser import LHRTool
    from app.core.matcher import match_issues
    from app.core.issue_merger import transform_to_simple_issues_with_insertions
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path}")
    print(f"项目根目录: {project_root}")
    sys.exit(1)

def save_json_file(data, filename, description):
    """保存数据到JSON文件"""
    output_dir = Path(__file__).parent / "pipeline_outputs"
    output_dir.mkdir(exist_ok=True)
    
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ {description} 已保存到: {filepath}")
    return filepath

def test_full_pipeline():
    """测试完整的SEO分析流程"""
    
    # 1. 读取测试HTML文件
    print("📖 读取测试HTML文件...")
    html_file_path = Path(__file__).parent / "test_seo_page.html"
    
    if not html_file_path.exists():
        print(f"❌ HTML文件不存在: {html_file_path}")
        return
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"✅ HTML文件读取成功，长度: {len(html_content)} 字符")
    
    # 2. 调用Lighthouse服务
    print("\n🔍 步骤1: 调用Lighthouse服务...")
    try:
        seo_service = SEOAnalysisService()
        lighthouse_result = seo_service._call_lighthouse_service(html_content)
        
        # 保存Lighthouse原始结果
        save_json_file(
            lighthouse_result, 
            "01_lighthouse_raw.json", 
            "Lighthouse原始结果"
        )
        
        print(f"✅ Lighthouse服务调用成功，SEO分数: {lighthouse_result.get('seoScore', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Lighthouse服务调用失败: {e}")
        return
    
    # 3. 运行LHR解析器
    print("\n📊 步骤2: 运行LHR解析器...")
    try:
        parser = LHRTool()
        parsed_result = parser.parse_lhr_json(lighthouse_result)
        
        # 保存解析后的结果
        save_json_file(
            parsed_result, 
            "02_parser_output.json", 
            "LHR解析器输出"
        )
        
        print(f"✅ 解析器运行成功，问题数量: {len(parsed_result.get('issues', []))}")
        
    except Exception as e:
        print(f"❌ 解析器运行失败: {e}")
        return
    
    # 4. 运行匹配器
    print("\n🎯 步骤3: 运行匹配器...")
    try:
        matched_result = match_issues(html_content, parsed_result)
        
        # 保存匹配结果
        save_json_file(
            matched_result, 
            "04_matcher_output.json", 
            "匹配器输出"
        )
        
        matched_issues = matched_result.get('issues', [])
        matched_count = len([i for i in matched_issues if i.get('match_status') == 'matched'])
        print(f"✅ 匹配器运行成功，总问题: {len(matched_issues)}, 已匹配: {matched_count}")
        
    except Exception as e:
        print(f"❌ 匹配器运行失败: {e}")
        return
    
    # 5. 运行问题合并器
    print("\n🔧 步骤4: 运行问题合并器...")
    try:
        merged_issues = transform_to_simple_issues_with_insertions(matched_result)
        
        # 保存合并结果
        save_json_file(
            merged_issues, 
            "04_merger_output.json", 
            "问题合并器输出"
        )
        
        print(f"✅ 问题合并器运行成功，合并后问题数量: {len(merged_issues)}")
        
    except Exception as e:
        print(f"❌ 问题合并器运行失败: {e}")
        return
    
    # 6. 构建最终结果
    print("\n📝 步骤5: 构建最终结果...")
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
            "最终SEO分析结果"
        )
        
        print(f"✅ 最终结果构建成功，SEO分数: {final_dict.get('seo_score', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 最终结果构建失败: {e}")
        return
    
    print("\n🎉 完整流程测试完成！")
    print("📁 所有中间结果文件已保存到 tests/pipeline_outputs/ 目录")
    print("\n📋 生成的文件:")
    print("  01_lighthouse_raw.json      - Lighthouse原始结果")
    print("  02_parser_output.json       - LHR解析器输出")
    print("  03_matcher_output.json      - 匹配器输出")
    print("  04_merger_output.json       - 问题合并器输出")
    print("  05_final_result.json        - 最终SEO分析结果")

if __name__ == "__main__":
    test_full_pipeline()
