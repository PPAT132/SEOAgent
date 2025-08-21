#!/usr/bin/env python3
"""
直接测试Lighthouse服务，看看它能检测到什么SEO问题
不调用LLM，只测试Lighthouse的检测能力
"""

import requests
import json
import os
from pathlib import Path

def test_lighthouse_detection():
    """测试Lighthouse能检测到什么SEO问题"""
    
    # 读取测试HTML文件
    test_file = Path(__file__).parent / "test_lighthouse_capabilities.html"
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"📄 测试HTML文件大小: {len(html_content)} 字符")
    print(f"📄 HTML预览: {html_content[:200]}...")
    
    # 调用Lighthouse服务
    lighthouse_url = "http://localhost:3002/audit-html"
    
    try:
        print(f"🔍 调用Lighthouse服务: {lighthouse_url}")
        response = requests.post(
            lighthouse_url,
            json={"html": html_content},
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ Lighthouse分析完成")
        print(f"📊 SEO分数: {result.get('seoScore', 'N/A')}")
        
        # 分析检测到的问题
        audits = result.get('audits', {})
        print(f"📋 总审计数量: {len(audits)}")
        
        # 找出所有失败的问题 (score = 0)
        failed_audits = []
        for audit_id, audit in audits.items():
            if audit.get('score') == 0:
                failed_audits.append({
                    'id': audit_id,
                    'title': audit.get('title', 'Unknown'),
                    'displayValue': audit.get('displayValue', ''),
                    'details': audit.get('details', {})
                })
        
        print(f"\n❌ 检测到的SEO问题 ({len(failed_audits)}个):")
        for i, audit in enumerate(failed_audits, 1):
            print(f"  {i}. {audit['id']}: {audit['title']}")
            if audit['displayValue']:
                print(f"     {audit['displayValue']}")
        
        # 保存结果到文件
        output_file = Path(__file__).parent / "pipeline_outputs" / "lighthouse_test_result.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 结果已保存到: {output_file}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Lighthouse服务调用失败: {e}")
        return None
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return None

if __name__ == "__main__":
    print("🧪 开始测试Lighthouse检测能力...")
    result = test_lighthouse_detection()
    
    if result:
        print("\n✅ 测试完成！")
    else:
        print("\n❌ 测试失败！")
