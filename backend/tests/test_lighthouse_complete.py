#!/usr/bin/env python3
"""
Complete Lighthouse Service Test - 测试完整的 Lighthouse 服务流程
读取 HTML 文件 -> Lighthouse 服务 -> Parser -> Matcher -> 输出结果
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Any, Dict, List

# 添加 core 模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'core'))

from lhr_parser import LHRTool
from matcher import match_issues
from result_processor import transform_matched_result

class LighthouseCompleteTester:
    def __init__(self, lighthouse_url: str = "http://localhost:3001"):
        self.lighthouse_url = lighthouse_url
        self.parser = LHRTool()

    def read_test_html(self, html_file_path: str) -> str:
        """读取测试 HTML 文件"""
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ HTML 文件未找到: {html_file_path}")
            return None
        except Exception as e:
            print(f"❌ 读取 HTML 文件错误: {e}")
            return None

    def call_lighthouse_service(self, html_content: str) -> Dict[str, Any]:
        """调用 Lighthouse 服务分析 HTML"""
        print("🔄 调用 Lighthouse 服务...")
        try:
            resp = requests.post(
                f"{self.lighthouse_url}/audit-html",
                json={"html": html_content},
                timeout=60
            )
            if resp.status_code != 200:
                print(f"❌ Lighthouse 服务错误: {resp.status_code}")
                print(f"响应: {resp.text}")
                return None

            result = resp.json()
            seo_score = result.get("seoScore")
            print(f"✅ Lighthouse 分析完成! SEO Score: {seo_score if seo_score is not None else 'N/A'}")
            return result

        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到 Lighthouse 服务: {self.lighthouse_url}")
            print("请确保 Lighthouse 服务在端口 3001 上运行")
            return None
        except requests.exceptions.Timeout:
            print("❌ Lighthouse 服务超时")
            return None
        except Exception as e:
            print(f"❌ 调用 Lighthouse 服务错误: {e}")
            return None

    def run_parser(self, lighthouse_result: Dict[str, Any]) -> Dict[str, Any]:
        """运行解析器，生成标准化的问题列表"""
        print("🔄 运行 LHR 解析器 (标准化问题)...")
        try:
            parsed = self.parser.parse_lhr_json(lighthouse_result)
            issues = parsed.get("issues", []) or []
            print(f"✅ 解析器完成! 标准化问题: {len(issues)}")
            return parsed
        except Exception as e:
            print(f"❌ 解析器错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run_matcher(self, html_content: str, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """运行匹配器，将问题映射到原始 HTML 的行数"""
        print("🔄 运行匹配器，在 HTML 中定位问题...")
        try:
            matched = match_issues(html_content, parsed_result)
            matched_issues = [it for it in matched.get("issues", []) if it.get("match_status") == "matched"]
            print(f"✅ 匹配器完成! 定位到 {len(matched_issues)} / {len(matched.get('issues', []))} 个问题")
            return matched
        except Exception as e:
            print(f"❌ 匹配器错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_simple_report(self, seo_score: Any, matched_result: Dict[str, Any], html_content: str) -> str:
        """生成简化的报告，只包含 seo_score 和 matched_result"""
        print("🔄 生成简化报告...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"lighthouse_complete_result_{timestamp}.json"
        
        # 生成 summary 数据（调试用，之后会删除）
        issues = matched_result.get("issues", [])
        matched_issues = [it for it in issues if it.get("match_status") == "matched"]
        matched_count = sum(1 for it in matched_issues if it.get("match_status") == "matched")
        
        # 按问题类型分组
        by_audit = {}
        for it in matched_issues:
            by_audit.setdefault(it.get("audit_id", "unknown"), []).append(it)
        
        summary = {
            "seo_score": seo_score,
            "total_issues_found": len(issues),
            "issues_located_in_html": matched_count,
            "issue_types_summary": {}
        }
        
        # 添加每种问题类型的详细信息
        for audit_id in sorted(by_audit.keys()):
            arr = by_audit[audit_id]
            summary["issue_types_summary"][audit_id] = {
                "count": len(arr),
                "sample_locations": []
            }
            
            # 添加前3个样本位置
            for i, hit in enumerate(arr[:3], 1):
                ls = hit.get("match_line_start", "N/A")
                le = hit.get("match_line_end", "N/A")
                html_preview = (hit.get("match_html") or "")
                if len(html_preview) > 80:
                    html_preview = html_preview[:80] + "..."
                
                summary["issue_types_summary"][audit_id]["sample_locations"].append({
                    "index": i,
                    "lines": f"{ls}-{le}",
                    "html_preview": html_preview
                })
        
        # 完全重新格式化 matched_result
        transformed_result = transform_matched_result(matched_result, html_content)
        
        # 报告结构（包含 summary 用于调试）
        report = {
            "seo_score": seo_score,
            "matched_result": transformed_result,  # 替换为新的格式
            "summary": summary  # 调试用，之后会删除
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✅ 报告保存到: {report_file}")
            return report_file
        except Exception as e:
            print(f"❌ 保存报告错误: {e}")
            return None

    def print_summary(self, seo_score: Any, matched_result: Dict[str, Any]):
        """打印结果摘要"""
        print("\n" + "="*60)
        print("📊 LIGHTHOUSE 完整测试结果摘要")
        print("="*60)
        
        print(f"SEO Score: {seo_score}")
        
        issues = matched_result.get("issues", [])
        matched_count = sum(1 for it in issues if it.get("match_status") == "matched")
        print(f"总问题数: {len(issues)}")
        print(f"成功定位: {matched_count}")
        
        # 按问题类型分组显示
        by_audit = {}
        for it in issues:
            audit_id = it.get("audit_id", "unknown")
            by_audit.setdefault(audit_id, []).append(it)
        
        if by_audit:
            print("\n问题类型和位置:")
            for audit_id in sorted(by_audit.keys()):
                arr = by_audit[audit_id]
                print(f"  • {audit_id}: {len(arr)} 个")
                # 显示前3个样本位置
                for i, hit in enumerate(arr[:3], 1):
                    ls = hit.get("match_line_start", "N/A")
                    le = hit.get("match_line_end", "N/A")
                    print(f"    [{i}] 行 {ls}-{le}")
                    html_preview = (hit.get("match_html") or "")
                    if len(html_preview) > 60:
                        html_preview = html_preview[:60] + "..."
                    if html_preview:
                        print(f"       HTML: {html_preview}")
        
        print("="*60)

    def run_complete_test(self, html_file_path: str) -> bool:
        """运行完整的测试流程"""
        print("🚀 开始 Lighthouse 完整测试")
        print("="*60)
        
        # 步骤1: 读取 HTML
        print(f"📄 读取 HTML 文件: {html_file_path}")
        html_content = self.read_test_html(html_file_path)
        if not html_content:
            return False
        print(f"✅ HTML 加载完成 ({len(html_content)} 字符)")
        
        # 步骤2: Lighthouse 服务
        print("\n🔍 调用 Lighthouse 服务...")
        lighthouse_result = self.call_lighthouse_service(html_content)
        if not lighthouse_result:
            print("❌ Lighthouse 服务调用失败")
            return False
        
        print(f"✅ Lighthouse 服务返回成功")
        print(f"   - 返回数据大小: {len(str(lighthouse_result))} 字符")
        print(f"   - 包含字段: {list(lighthouse_result.keys())}")
        
        # 详细检查 Lighthouse 返回数据
        if 'audits' in lighthouse_result:
            audits = lighthouse_result['audits']
            print(f"   - 审计总数: {len(audits)}")
            
            # 检查失败的审计
            failed_audits = []
            for audit_id, audit in audits.items():
                if hasattr(audit, 'score') and audit.score is not None and audit.score < 1:
                    failed_audits.append(audit_id)
            
            print(f"   - 失败的审计: {len(failed_audits)}")
            if failed_audits:
                print(f"   - 失败审计类型: {failed_audits[:5]}")  # 显示前5个
        
        if 'seoScore' in lighthouse_result:
            print(f"   - 原始 SEO Score: {lighthouse_result['seoScore']}")
        
        # 步骤3: 解析器 (标准化问题)
        print("\n📊 运行 LHR 解析器...")
        parsed_result = self.run_parser(lighthouse_result)
        if not parsed_result:
            print("❌ LHR 解析器运行失败")
            return False
        
        print(f"✅ LHR 解析器运行成功")
        print(f"   - SEO Score: {parsed_result.get('seo_score')}")
        print(f"   - 解析到的问题数: {len(parsed_result.get('issues', []))}")
        print(f"   - 问题类型: {[issue.get('audit_id') for issue in parsed_result.get('issues', [])]}")
        
        # 步骤4: 匹配器 (映射到原始行数)
        print("\n🎯 运行匹配器...")
        matched_result = self.run_matcher(html_content, parsed_result)
        if not matched_result:
            print("❌ 匹配器运行失败")
            return False
        
        print(f"✅ 匹配器运行成功")
        print(f"   - 匹配结果大小: {len(str(matched_result))} 字符")
        print(f"   - 总问题数: {len(matched_result.get('issues', []))}")
        
        # 统计匹配状态
        issues = matched_result.get("issues", [])
        matched_count = sum(1 for it in issues if it.get("match_status") == "matched")
        unmatched_count = sum(1 for it in issues if it.get("match_status") != "matched")
        print(f"   - 成功匹配: {matched_count}")
        print(f"   - 匹配失败: {unmatched_count}")
        
        # 步骤5: 生成简化报告
        print("\n📝 生成报告...")
        seo_score = parsed_result.get("seo_score")
        report_file = self.generate_simple_report(seo_score, matched_result, html_content)
        
        # 步骤6: 打印摘要
        self.print_summary(seo_score, matched_result)
        
        if report_file:
            print(f"\n📋 完整报告保存到: {report_file}")
            print("打开文件查看详细的匹配结果")
        
        return True

def main():
    """主入口"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_html_file = os.path.join(script_dir, "test_seo_page.html")
    
    if not os.path.exists(default_html_file):
        print(f"❌ 测试 HTML 文件未找到: {default_html_file}")
        print("请确保 HTML 文件存在于 tests 目录中")
        return
    
    tester = LighthouseCompleteTester()
    ok = tester.run_complete_test(default_html_file)
    
    if ok:
        print("\n🎉 测试完成!")
    else:
        print("\n💥 测试失败!")
        print("\n故障排除提示:")
        print("1) 确保 Lighthouse 服务正在运行: cd ../lighthouse-service && node server.js")
        print("2) 检查端口 3001 是否可用")
        print("3) 验证 HTML 文件存在且可读")

if __name__ == "__main__":
    main()
