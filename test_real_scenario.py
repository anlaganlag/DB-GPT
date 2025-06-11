#!/usr/bin/env python3
"""
真实场景测试脚本
Real Scenario Test Script

模拟实际的DB-GPT使用场景，测试双模式输出功能
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

def test_overdue_rate_analysis():
    """测试逾期率分析场景（最常用的场景）"""
    print("\n" + "="*60)
    print("🧪 真实场景测试: 逾期率分析")
    print("="*60)
    
    # 模拟真实的逾期率数据
    test_data = pd.DataFrame({
        'loan_month': ['2024-10', '2024-11', '2024-12', '2025-01'],
        'MOB_1': [0.0234, 0.0267, 0.0198, 0.0245],
        'MOB_2': [0.0456, 0.0523, 0.0398, 0.0467],
        'MOB_3': [0.0678, 0.0734, 0.0612, 0.0689],
        'MOB_6': [0.1234, 0.1345, 0.1156, 0.1278],
        'MOB_12': [0.1876, 0.1987, 0.1734, 0.1845]
    })
    
    # 模拟AI生成的prompt response
    mock_prompt_response = SqlAction(
        sql="""
        SELECT 
            loan_month,
            MOB_1,
            MOB_2, 
            MOB_3,
            MOB_6,
            MOB_12
        FROM overdue_rate_stats 
        WHERE loan_month >= '2024-10'
        ORDER BY loan_month
        """,
        thoughts={},
        display="",
        direct_response="",
        missing_info="",
        analysis_report={
            'summary': '近4个月逾期率分析显示整体风险控制良好，但需关注季节性波动',
            'key_findings': [
                '2024年11月逾期率达到峰值，各MOB期数均为最高',
                '2024年12月逾期率显著下降，可能与年末风控收紧有关',
                '2025年1月逾期率回升，需持续监控',
                'MOB_12期数逾期率接近20%，属于行业正常水平',
                '短期MOB（1-3个月）逾期率控制在7%以下'
            ],
            'insights': [
                '11月份可能存在放款质量问题或外部经济环境影响',
                '12月份的风控措施效果显著，值得总结推广',
                '长期逾期率（MOB_12）趋势稳定，风控策略有效',
                '季节性因素对逾期率有明显影响，需要动态调整策略'
            ],
            'recommendations': [
                '深入分析11月份放款批次的特征，识别风险因素',
                '将12月份的成功风控经验制度化',
                '建立季节性风控调整机制',
                '加强对MOB_6-12期数客户的跟踪管理',
                '考虑在特定月份提高风控标准'
            ],
            'methodology': '基于月度放款批次的逾期率统计分析，采用MOB（Months on Books）方法追踪不同期数的逾期表现'
        }
    )
    
    # 创建解析器
    parser = DbChatOutputParser()
    
    # 模拟数据查询函数
    def mock_data_func(sql):
        return test_data
    
    print("📋 用户查询: '帮我分析最近几个月的逾期率情况'")
    print("🤖 AI生成SQL并执行查询...")
    
    try:
        # 测试默认模式（Simple）
        print("\n🔍 默认模式输出（Simple - Markdown格式）:")
        print("-" * 50)
        simple_result = parser.parse_view_response("", mock_data_func, mock_prompt_response)
        print(simple_result)
        
        # 测试Enhanced模式
        print("\n\n🔍 Enhanced模式输出（chart-view格式）:")
        print("-" * 50)
        enhanced_result = parser.parse_view_response("", mock_data_func, mock_prompt_response, mode="enhanced")
        print(enhanced_result[:200] + "..." if len(enhanced_result) > 200 else enhanced_result)
        
        # 验证结果
        simple_checks = [
            "📊 **查询结果**" in simple_result,
            "MOB_1" in simple_result and "MOB_12" in simple_result,
            "```sql" in simple_result,
            "📋 **分析报告**" in simple_result,
            "近4个月逾期率分析" in simple_result
        ]
        
        enhanced_checks = [
            "<chart-view" in enhanced_result,
            "content=" in enhanced_result,
            "response_table" in enhanced_result
        ]
        
        print(f"\n✅ Simple模式验证: {all(simple_checks)} ({sum(simple_checks)}/5)")
        print(f"✅ Enhanced模式验证: {all(enhanced_checks)} ({sum(enhanced_checks)}/3)")
        
        return all(simple_checks) and all(enhanced_checks)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_empty_result_scenario():
    """测试空结果场景"""
    print("\n" + "="*60)
    print("🧪 真实场景测试: 空结果处理")
    print("="*60)
    
    # 模拟空结果
    empty_data = pd.DataFrame()
    
    mock_prompt_response = SqlAction(
        sql="SELECT * FROM overdue_rate_stats WHERE loan_month = '2030-01'",
        thoughts={},
        display="",
        direct_response="",
        missing_info="",
        analysis_report={
            'summary': '查询的时间范围内暂无数据',
            'key_findings': ['指定月份暂无放款记录'],
            'insights': ['可能是未来月份或系统维护期间'],
            'recommendations': ['检查查询条件或选择其他时间范围']
        }
    )
    
    parser = DbChatOutputParser()
    
    def mock_empty_data_func(sql):
        return empty_data
    
    try:
        print("📋 用户查询: '查询2030年1月的逾期率'")
        print("🤖 AI生成SQL但查询结果为空...")
        
        # 测试空结果的Simple模式
        result = parser.parse_view_response("", mock_empty_data_func, mock_prompt_response)
        print("\n📋 空结果处理输出:")
        print("-" * 40)
        print(result)
        
        # 验证空结果处理
        checks = [
            "查询执行成功" in result,
            "没有找到匹配的数据" in result,
            "```sql" in result,
            "2030-01" in result
        ]
        
        print(f"\n✅ 空结果处理验证: {all(checks)} ({sum(checks)}/4)")
        return all(checks)
        
    except Exception as e:
        print(f"❌ 空结果测试失败: {e}")
        return False

def test_sql_error_scenario():
    """测试SQL错误场景"""
    print("\n" + "="*60)
    print("🧪 真实场景测试: SQL错误处理")
    print("="*60)
    
    # 模拟SQL错误的prompt response
    mock_prompt_response = SqlAction(
        sql="SELECT * FROM non_existent_table WHERE invalid_column = 'test'",
        thoughts={},
        display="",
        direct_response="",
        missing_info="",
        analysis_report={}
    )
    
    parser = DbChatOutputParser()
    
    def mock_error_data_func(sql):
        # 模拟SQL执行错误
        raise Exception("Table 'overdue_analysis.non_existent_table' doesn't exist")
    
    try:
        print("📋 用户查询: '查询不存在的表'")
        print("🤖 AI生成了错误的SQL...")
        
        # 测试SQL错误处理
        result = parser.parse_view_response("", mock_error_data_func, mock_prompt_response)
        print("\n📋 SQL错误处理输出:")
        print("-" * 40)
        print(result)
        
        # 验证错误处理
        checks = [
            "数据库查询详细信息" in result,
            "查询失败" in result,
            "```sql" in result,
            "non_existent_table" in result,
            "建议" in result
        ]
        
        print(f"\n✅ SQL错误处理验证: {all(checks)} ({sum(checks)}/5)")
        return all(checks)
        
    except Exception as e:
        print(f"❌ SQL错误测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始真实场景测试")
    print("="*60)
    print("测试双模式输出功能在实际使用场景中的表现")
    
    # 运行所有测试
    test1_passed = test_overdue_rate_analysis()
    test2_passed = test_empty_result_scenario()
    test3_passed = test_sql_error_scenario()
    
    print("\n" + "="*60)
    print("🎯 真实场景测试总结")
    print("="*60)
    print(f"   逾期率分析场景: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"   空结果处理场景: {'✅ 通过' if test2_passed else '❌ 失败'}")
    print(f"   SQL错误处理场景: {'✅ 通过' if test3_passed else '❌ 失败'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 所有真实场景测试通过!")
        print("\n📋 验证结果:")
        print("   ✅ 双模式输出功能在实际场景中工作正常")
        print("   ✅ Simple模式提供优秀的用户体验")
        print("   ✅ Enhanced模式支持前端渲染")
        print("   ✅ 错误处理机制完善")
        print("   ✅ 空结果处理友好")
        print("\n🚀 功能已准备好投入生产使用!")
        return 0
    else:
        print("\n⚠️ 部分真实场景测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    exit(main()) 