#!/usr/bin/env python3
"""
Test script to verify analysis report display when query results are empty
测试查询结果为空时仍显示分析报告的脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'packages/dbgpt-app/src'))

from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser, SqlAction

def test_empty_result_with_analysis_report():
    """Test that analysis reports are shown even when query results are empty"""
    
    print("🧪 Testing Empty Result with Analysis Report...")
    print("="*60)
    
    # Create parser instance
    parser = DbChatOutputParser()
    
    # Create a mock SqlAction with SQL and analysis_report
    mock_response = SqlAction(
        sql="SELECT * FROM loans WHERE overdue_date = '2023-05-01' AND status = 'overdue'",
        thoughts="Analyzing overdue data for May",
        display="response_table",
        direct_response="I will analyze the overdue data for May.",
        missing_info="",
        analysis_report={
            "summary": "分析5月份逾期数据以识别根本原因",
            "key_findings": [
                "查询执行成功但未找到匹配的逾期记录",
                "可能的原因包括数据筛选条件过于严格",
                "建议调整查询条件或检查数据完整性"
            ],
            "insights": [
                "5月份可能没有符合特定条件的逾期案例",
                "这可能表明风控措施有效",
                "或者数据记录存在时间延迟"
            ],
            "recommendations": [
                "扩大查询时间范围以获取更多数据",
                "检查数据源的完整性和及时性",
                "考虑调整逾期定义标准",
                "与数据团队确认数据更新频率"
            ],
            "methodology": "使用SQL查询分析特定时间段的逾期数据，通过多维度筛选条件识别潜在的根本原因"
        }
    )
    
    # Mock data function that returns empty DataFrame
    def mock_empty_data_function(sql):
        import pandas as pd
        return pd.DataFrame()  # Empty result
    
    # Test the parse_view_response method with empty result
    print("📝 Testing parse_view_response with empty result but analysis_report...")
    
    result = parser.parse_view_response(
        speak="Test speak",
        data=mock_empty_data_function,
        prompt_response=mock_response
    )
    
    print("\n🔍 Result:")
    print("-" * 40)
    print(result)
    print("-" * 40)
    
    # Verify the result contains both empty message and analysis report
    success_checks = [
        ("查询执行成功，但没有找到匹配的数据" in result, "Contains empty result message"),
        ("📋 **分析报告**" in result, "Contains analysis report header"),
        ("📝 分析摘要" in result, "Contains summary section"),
        ("🔍 关键发现" in result, "Contains key findings"),
        ("💡 业务洞察" in result, "Contains insights"),
        ("🎯 建议措施" in result, "Contains recommendations"),
        ("🔬 分析方法" in result, "Contains methodology"),
        ("查询执行成功但未找到匹配的逾期记录" in result, "Contains specific finding"),
        ("扩大查询时间范围以获取更多数据" in result, "Contains specific recommendation"),
        ("I will analyze the overdue data for May." not in result, "Does NOT show direct_response only")
    ]
    
    print("\n✅ Verification Results:")
    all_passed = True
    for check, description in success_checks:
        status = "✅ PASS" if check else "❌ FAIL"
        print(f"  {status}: {description}")
        if not check:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Empty result with analysis report works correctly.")
        print("✅ Users will see analysis reports even when no data is found.")
    else:
        print("❌ SOME TESTS FAILED! The fix may need additional work.")
    
    return all_passed

def test_empty_result_without_analysis_report():
    """Test fallback behavior when there's no analysis report"""
    
    print("\n🧪 Testing Empty Result without Analysis Report...")
    print("="*60)
    
    parser = DbChatOutputParser()
    
    # Create a mock SqlAction with SQL but no analysis_report
    mock_response = SqlAction(
        sql="SELECT * FROM simple_table",
        thoughts="Simple query",
        display="response_table",
        direct_response="Simple query result.",
        missing_info="",
        analysis_report={}  # Empty analysis report
    )
    
    def mock_empty_data_function(sql):
        import pandas as pd
        return pd.DataFrame()
    
    result = parser.parse_view_response(
        speak="Test speak",
        data=mock_empty_data_function,
        prompt_response=mock_response
    )
    
    print(f"📝 Result: {result}")
    
    # Should show simple empty message without analysis report
    expected_content = "查询执行成功，但没有找到匹配的数据"
    has_expected = expected_content in result
    no_analysis_report = "📋 **分析报告**" not in result
    
    success = has_expected and no_analysis_report
    
    print(f"\n✅ Fallback Test: {'PASS' if success else 'FAIL'}")
    if success:
        print("✅ Simple empty message works when no analysis report is available.")
    else:
        print("❌ Fallback behavior is not working as expected.")
    
    return success

if __name__ == "__main__":
    print("🚀 Starting Empty Result Analysis Report Tests...")
    print("="*80)
    
    test1_passed = test_empty_result_with_analysis_report()
    test2_passed = test_empty_result_without_analysis_report()
    
    print("\n" + "="*80)
    print("📊 FINAL RESULTS:")
    print(f"  Empty Result + Analysis Report: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Empty Result + No Analysis Report: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! Empty result handling is working correctly.")
        print("🔧 Users will see analysis reports even when no data is found.")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED! Please check the implementation.")
        sys.exit(1) 