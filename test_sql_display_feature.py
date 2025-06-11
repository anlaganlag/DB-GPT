#!/usr/bin/env python3
"""
测试SQL显示功能
Test SQL Display Feature

验证在查询结果中显示SQL语句的功能是否正常工作
"""

import sys
import os
import pandas as pd
from collections import namedtuple

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'dbgpt-app', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'dbgpt-core', 'src'))

try:
    from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser
    print("✅ 成功导入 DbChatOutputParser")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# Create a mock SqlAction for testing
SqlAction = namedtuple('SqlAction', ['sql', 'thoughts', 'display', 'direct_response', 'missing_info', 'analysis_report'])

def test_sql_display_with_results():
    """测试有查询结果时的SQL显示"""
    print("\n" + "="*60)
    print("🧪 测试1: 有查询结果时的SQL显示")
    print("="*60)
    
    # Create test data
    test_data = pd.DataFrame({
        'loan_month': ['2025-01', '2025-02', '2025-03'],
        'MOB_1': [0.05, 0.06, 0.04],
        'MOB_2': [0.08, 0.09, 0.07],
        'MOB_3': [0.12, 0.13, 0.11]
    })
    
    # Create mock prompt response with SQL and analysis report
    mock_prompt_response = SqlAction(
        sql="SELECT loan_month, MOB_1, MOB_2, MOB_3 FROM overdue_rate_stats WHERE loan_month >= '2025-01'",
        thoughts={},
        display="",
        direct_response="",
        missing_info="",
        analysis_report={
            'summary': '逾期率分析显示2025年前三个月的逾期情况',
            'key_findings': [
                '2025年2月的逾期率最高',
                '各MOB期数的逾期率呈递增趋势'
            ],
            'insights': [
                '需要关注2月份放款质量',
                'MOB_3期数的风险控制需要加强'
            ],
            'recommendations': [
                '加强2月份放款审核',
                '优化风控模型'
            ],
            'methodology': '基于历史数据的逾期率统计分析'
        }
    )
    
    # Create parser and test
    parser = DbChatOutputParser()
    
    try:
        result = parser._format_result_for_display(test_data, mock_prompt_response)
        print("✅ 格式化成功")
        print("\n📋 格式化结果:")
        print("-" * 40)
        print(result)
        
        # Check if SQL is displayed
        if "🔧 **执行的SQL查询**" in result and "```sql" in result:
            print("\n✅ SQL显示功能正常工作")
        else:
            print("\n❌ SQL显示功能未正常工作")
            
        # Check if analysis report is displayed
        if "📋 **分析报告**" in result:
            print("✅ 分析报告显示正常")
        else:
            print("❌ 分析报告显示异常")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_sql_display_empty_results():
    """测试空结果时的SQL显示"""
    print("\n" + "="*60)
    print("🧪 测试2: 空结果时的SQL显示")
    print("="*60)
    
    # Create empty test data
    test_data = pd.DataFrame()
    
    # Create mock prompt response with SQL and analysis report
    mock_prompt_response = SqlAction(
        sql="SELECT * FROM overdue_rate_stats WHERE loan_month = '2025-12'",
        thoughts={},
        display="",
        direct_response="",
        missing_info="",
        analysis_report={
            'summary': '查询2025年12月的数据，但该月份暂无数据',
            'key_findings': ['目标月份暂无放款数据'],
            'insights': ['可能是未来月份或数据尚未录入'],
            'recommendations': ['检查数据录入情况或调整查询时间范围']
        }
    )
    
    # Create parser and test
    parser = DbChatOutputParser()
    
    # Mock the data function for empty results
    def mock_data_func(sql):
        return pd.DataFrame()  # Return empty DataFrame
    
    try:
        result = parser.parse_view_response("", mock_data_func, mock_prompt_response)
        print("✅ 解析成功")
        print("\n📋 解析结果:")
        print("-" * 40)
        print(result)
        
        # Check if SQL is displayed
        if "🔧 **执行的SQL查询**" in result and "```sql" in result:
            print("\n✅ 空结果时SQL显示功能正常工作")
        else:
            print("\n❌ 空结果时SQL显示功能未正常工作")
            
        # Check if analysis report is displayed
        if "📋 **分析报告**" in result:
            print("✅ 空结果时分析报告显示正常")
        else:
            print("❌ 空结果时分析报告显示异常")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_sql_display_without_analysis():
    """测试只有SQL没有分析报告时的显示"""
    print("\n" + "="*60)
    print("🧪 测试3: 只有SQL没有分析报告时的显示")
    print("="*60)
    
    # Create test data
    test_data = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['张三', '李四', '王五'],
        'amount': [1000, 2000, 1500]
    })
    
    # Create mock prompt response with only SQL
    mock_prompt_response = SqlAction(
        sql="SELECT id, name, amount FROM customers LIMIT 3",
        thoughts={},
        display="",
        direct_response="",
        missing_info="",
        analysis_report={}  # Empty analysis report
    )
    
    # Create parser and test
    parser = DbChatOutputParser()
    
    try:
        result = parser._format_result_for_display(test_data, mock_prompt_response)
        print("✅ 格式化成功")
        print("\n📋 格式化结果:")
        print("-" * 40)
        print(result)
        
        # Check if SQL is displayed
        if "🔧 **执行的SQL查询**" in result and "```sql" in result:
            print("\n✅ 只有SQL时显示功能正常工作")
        else:
            print("\n❌ 只有SQL时显示功能未正常工作")
            
        # Check that analysis report is not displayed when empty
        if "📋 **分析报告**" not in result:
            print("✅ 空分析报告时正确不显示分析部分")
        else:
            print("❌ 空分析报告时错误显示了分析部分")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("🚀 开始测试SQL显示功能")
    print("="*60)
    
    # Run all tests
    test_sql_display_with_results()
    test_sql_display_empty_results()
    test_sql_display_without_analysis()
    
    print("\n" + "="*60)
    print("🎯 测试总结")
    print("="*60)
    print("✅ 所有测试已完成")
    print("📋 功能验证:")
    print("   - 查询结果 + SQL + 分析报告的完整显示")
    print("   - 空结果 + SQL + 分析报告的显示")
    print("   - 只有SQL没有分析报告的显示")
    print("   - SQL语句的格式化和说明")
    print("   - 各种情况下的用户体验优化")

if __name__ == "__main__":
    main() 