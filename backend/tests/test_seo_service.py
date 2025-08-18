#!/usr/bin/env python3
"""
测试 SEO Analysis Service
验证完整的 SEO 分析流程
"""

import os
import sys
import json
from datetime import datetime

# 添加 app 模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.seo_analysis_service import SEOAnalysisService, analyze_html_file


def test_seo_service():
    """测试 SEO 分析服务"""
    print("🧪 开始测试 SEO Analysis Service")
    print("="*60)
    
    # 获取测试 HTML 文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_file_path = os.path.join(script_dir, "test_seo_page.html")
    
    if not os.path.exists(html_file_path):
        print(f"❌ 测试 HTML 文件未找到: {html_file_path}")
        return False
    
    try:
        # 创建服务实例
        service = SEOAnalysisService()
        
        # 分析 HTML 文件
        print(f"📄 分析 HTML 文件: {html_file_path}")
        result = service.analyze_html_file(html_file_path)
        
        # 显示结果摘要
        print(f"\n📊 分析结果摘要:")
        print(f"SEO Score: {result.seo_score}")
        print(f"总行数: {result.total_lines}")
        print(f"问题数量: {len(result.issues)}")
        
        # 显示每个问题的信息
        for i, issue in enumerate(result.issues, 1):
            print(f"\n{i}. 问题: {issue.title}")
            print(f"   行范围: {issue.start_line}-{issue.end_line}")
            print(f"   HTML: {issue.raw_html}")
        
        # 保存结果到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"seo_service_result_{timestamp}.json"
        
        # 转换为字典并保存
        result_dict = result.dict()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 测试完成!")
        print(f"结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_convenience_functions():
    """测试便捷函数"""
    print("\n🧪 测试便捷函数")
    print("="*60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_file_path = os.path.join(script_dir, "test_seo_page.html")
    
    try:
        # 测试便捷函数
        result = analyze_html_file(html_file_path)
        print(f"✅ 便捷函数测试成功!")
        print(f"SEO Score: {result.seo_score}")
        print(f"问题数量: {len(result.issues)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 便捷函数测试失败: {e}")
        return False


def main():
    """主入口"""
    print("🚀 SEO Analysis Service 测试")
    print("="*60)
    
    # 测试主服务
    service_ok = test_seo_service()
    
    # 测试便捷函数
    convenience_ok = test_convenience_functions()
    
    if service_ok and convenience_ok:
        print("\n🎉 所有测试通过!")
    else:
        print("\n💥 部分测试失败!")
    
    print("\n故障排除提示:")
    print("1) 确保 Lighthouse 服务正在运行: cd ../lighthouse-service && node server.js")
            print("2) 检查端口 3002 是否可用")
    print("3) 验证 HTML 文件存在且可读")


if __name__ == "__main__":
    main()
