#!/usr/bin/env python3
"""
测试 Dummy 数据处理逻辑
测试行范围重叠合并功能
"""

import os
import sys

# 添加 core 模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app', 'core'))

from result_processor import test_dummy_data

def main():
    """主入口"""
    print("🧪 开始测试 Dummy 数据处理逻辑")
    print("="*60)
    
    # 运行测试
    result = test_dummy_data()
    
    print(f"\n🎉 测试完成!")
    print(f"最终生成了 {len(result)} 个行范围")
    
    # 验证结果
    expected_ranges = [
        (60, 70),  # 最大结束行号，应该排第一
        (40, 55),  # 合并后的范围
        (10, 30),  # 合并后的范围
    ]
    
    print(f"\n✅ 验证结果:")
    for i, (expected_start, expected_end) in enumerate(expected_ranges):
        if i < len(result):
            actual = result[i]
            if actual['start_line'] == expected_start and actual['end_line'] == expected_end:
                print(f"  ✓ 范围 {i+1}: {expected_start}-{expected_end} ✓")
            else:
                print(f"  ✗ 范围 {i+1}: 期望 {expected_start}-{expected_end}, 实际 {actual['start_line']}-{actual['end_line']} ✗")
        else:
            print(f"  ✗ 范围 {i+1}: 期望 {expected_start}-{expected_end}, 但结果中不存在 ✗")

if __name__ == "__main__":
    main()
