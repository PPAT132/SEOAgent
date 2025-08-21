#!/usr/bin/env python3
"""
全面分析Lighthouse检测能力
"""

import json
from pathlib import Path

def analyze_lighthouse_results():
    """分析Lighthouse测试结果"""
    
    result_file = Path(__file__).parent / "pipeline_outputs" / "lighthouse_test_result.json"
    
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 SEO分数: {data.get('seoScore', 'N/A')}")
    
    audits = data.get('audits', {})
    print(f"📋 总审计数量: {len(audits)}")
    
    # 分类分析
    failed_audits = []
    passed_audits = []
    not_applicable = []
    
    for audit_id, audit in audits.items():
        score = audit.get('score')
        title = audit.get('title', 'Unknown')
        
        if score == 0:
            failed_audits.append({
                'id': audit_id,
                'title': title,
                'displayValue': audit.get('displayValue', ''),
                'details': audit.get('details', {})
            })
        elif score == 1:
            passed_audits.append({
                'id': audit_id,
                'title': title
            })
        else:
            not_applicable.append({
                'id': audit_id,
                'title': title,
                'score': score
            })
    
    print(f"\n❌ 失败的审计 ({len(failed_audits)}个):")
    for i, audit in enumerate(failed_audits, 1):
        print(f"  {i}. {audit['id']}: {audit['title']}")
        if audit['displayValue']:
            print(f"     {audit['displayValue']}")
    
    print(f"\n✅ 通过的审计 ({len(passed_audits)}个):")
    for i, audit in enumerate(passed_audits, 1):
        print(f"  {i}. {audit['id']}: {audit['title']}")
    
    print(f"\n⚠️ 其他审计 ({len(not_applicable)}个):")
    for i, audit in enumerate(not_applicable, 1):
        print(f"  {i}. {audit['id']}: {audit['title']} (分数: {audit['score']})")
    
    # 详细分析失败的问题
    print(f"\n🔍 失败问题的详细分析:")
    for audit in failed_audits:
        print(f"\n  {audit['id']}: {audit['title']}")
        
        details = audit.get('details', {})
        if 'items' in details:
            items = details['items']
            print(f"    检测到 {len(items)} 个问题:")
            for j, item in enumerate(items, 1):
                if 'node' in item:
                    node = item['node']
                    snippet = node.get('snippet', 'N/A')
                    selector = node.get('selector', 'N/A')
                    print(f"      {j}. {selector}")
                    print(f"         HTML: {snippet}")
                elif 'href' in item and 'text' in item:
                    print(f"      {j}. 链接: {item['href']} -> '{item['text']}'")
                elif 'index' in item and 'line' in item:
                    print(f"      {j}. 行 {item['index']}: {item['line']} - {item.get('message', '')}")

if __name__ == "__main__":
    print("🔍 全面分析Lighthouse检测结果...")
    analyze_lighthouse_results()
