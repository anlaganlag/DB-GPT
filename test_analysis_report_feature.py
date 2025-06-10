#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分析报告功能的脚本
验证新的analysis_report字段是否正常工作
"""

import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'dbgpt-app', 'src'))

from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser, SqlAction

def test_analysis_report_parsing():
    """测试分析报告的解析功能"""
    print("🧪 测试分析报告解析功能...")
    
    # 创建解析器
    parser = DbChatOutputParser()
    
    # 测试包含分析报告的JSON响应
    test_json_with_report = {
        "thoughts": "用户需要分析5月份的逾期数据，并找出逾期的根因",
        "direct_response": "以下是5月份的逾期数据分析结果",
        "sql": "SELECT * FROM overdue_rate_stats WHERE loan_month = '2023-05' LIMIT 10",
        "display_type": "Table",
        "analysis_report": {
            "summary": "5月份逾期率分析显示整体逾期情况相对稳定，但在某些MOB期数存在异常",
            "key_findings": [
                "MOB1期的逾期率为2.5%，低于行业平均水平",
                "MOB6期的逾期率达到15.8%，需要重点关注",
                "DPD30+的逾期金额占总逾期金额的78%"
            ],
            "insights": [
                "早期MOB期数的风控效果良好，说明初期筛选机制有效",
                "中后期MOB期数逾期率上升，可能与客户还款能力变化有关",
                "长期逾期（DPD30+）是主要风险来源"
            ],
            "recommendations": [
                "加强MOB6期客户的跟踪和提醒",
                "优化中后期风险预警机制",
                "针对DPD30+客户制定专门的催收策略"
            ],
            "methodology": "基于overdue_rate_stats表的历史数据，按MOB期数和DPD阈值进行分层分析"
        }
    }
    
    # 测试不包含分析报告的JSON响应
    test_json_without_report = {
        "thoughts": "简单查询逾期数据",
        "direct_response": "查询结果如下",
        "sql": "SELECT * FROM overdue_rate_stats LIMIT 5",
        "display_type": "Table"
    }
    
    # 测试解析包含报告的JSON
    print("\n1. 测试包含分析报告的JSON解析...")
    json_str_with_report = json.dumps(test_json_with_report, ensure_ascii=False)
    result_with_report = parser.parse_prompt_response(json_str_with_report)
    
    print(f"✅ 解析成功")
    print(f"📊 SQL: {result_with_report.sql}")
    print(f"💭 Thoughts: {result_with_report.thoughts}")
    print(f"📋 Analysis Report Keys: {list(result_with_report.analysis_report.keys())}")
    print(f"📝 Summary: {result_with_report.analysis_report.get('summary', 'N/A')}")
    
    # 测试解析不包含报告的JSON
    print("\n2. 测试不包含分析报告的JSON解析...")
    json_str_without_report = json.dumps(test_json_without_report, ensure_ascii=False)
    result_without_report = parser.parse_prompt_response(json_str_without_report)
    
    print(f"✅ 解析成功")
    print(f"📊 SQL: {result_without_report.sql}")
    print(f"💭 Thoughts: {result_without_report.thoughts}")
    print(f"📋 Analysis Report: {result_without_report.analysis_report}")
    
    return True

def test_result_formatting():
    """测试结果格式化功能"""
    print("\n🧪 测试结果格式化功能...")
    
    # 创建解析器
    parser = DbChatOutputParser()
    
    # 模拟查询结果
    import pandas as pd
    mock_result = pd.DataFrame({
        'stat_date': ['2023-05-01', '2023-05-02', '2023-05-03'],
        'loan_month': ['2023-05', '2023-05', '2023-05'],
        'mob': [1, 1, 1],
        'total_loans': [1000, 1050, 1100],
        'overdue_loans': [25, 28, 30],
        'overdue_rate': [0.025, 0.0267, 0.0273]
    })
    
    # 创建包含分析报告的响应
    mock_response = SqlAction(
        sql="SELECT * FROM overdue_rate_stats WHERE loan_month = '2023-05'",
        thoughts="分析5月份逾期数据",
        display="Table",
        direct_response="",
        missing_info="",
        analysis_report={
            "summary": "5月份逾期率整体稳定，略有上升趋势",
            "key_findings": [
                "逾期率从2.5%上升到2.73%",
                "总贷款数持续增长"
            ],
            "insights": [
                "逾期率上升可能与新增贷款质量有关"
            ],
            "recommendations": [
                "加强新客户风险评估"
            ],
            "methodology": "时间序列分析"
        }
    )
    
    # 测试格式化
    formatted_result = parser._format_result_for_display(mock_result, mock_response)
    
    print("✅ 格式化成功")
    print("📋 格式化结果预览:")
    print("-" * 60)
    print(formatted_result[:500] + "..." if len(formatted_result) > 500 else formatted_result)
    print("-" * 60)
    
    # 检查是否包含分析报告部分
    if "分析报告" in formatted_result:
        print("✅ 分析报告部分已包含在格式化结果中")
    else:
        print("❌ 分析报告部分未包含在格式化结果中")
        return False
    
    return True

def test_prompt_format():
    """测试新的prompt格式"""
    print("\n🧪 测试新的prompt格式...")
    
    from dbgpt_app.scene.chat_db.auto_execute.prompt import RESPONSE_FORMAT_SIMPLE
    
    print("✅ 新的响应格式:")
    print(json.dumps(RESPONSE_FORMAT_SIMPLE, indent=2, ensure_ascii=False))
    
    # 检查是否包含analysis_report字段
    if "analysis_report" in RESPONSE_FORMAT_SIMPLE:
        print("✅ analysis_report字段已添加到响应格式中")
        
        report_structure = RESPONSE_FORMAT_SIMPLE["analysis_report"]
        expected_keys = ["summary", "key_findings", "insights", "recommendations", "methodology"]
        
        for key in expected_keys:
            if key in report_structure:
                print(f"✅ {key} 字段存在")
            else:
                print(f"❌ {key} 字段缺失")
                return False
    else:
        print("❌ analysis_report字段未添加到响应格式中")
        return False
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试分析报告功能...")
    print("="*60)
    
    tests = [
        ("Prompt格式测试", test_prompt_format),
        ("JSON解析测试", test_analysis_report_parsing),
        ("结果格式化测试", test_result_formatting),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            if test_func():
                print(f"✅ {test_name} 通过")
                passed += 1
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print("\n" + "="*60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！分析报告功能已成功实现")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 