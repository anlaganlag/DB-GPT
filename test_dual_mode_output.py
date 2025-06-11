#!/usr/bin/env python3
"""
测试双模式输出功能
Test Dual-Mode Output Feature

验证simple模式（默认Markdown格式）和enhanced模式（chart-view格式）的功能
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

def test_simple_mode_output():
    """测试Simple模式输出（默认Markdown格式）"""
    print("\n" + "="*60)
    print("🧪 测试1: Simple模式输出（默认Markdown格式）")
    print("="*60)
    
    # Create test data
    test_data = pd.DataFrame({
        'loan_month': ['2025-01', '2025-02', '2025-03'],
        'MOB_1': [0.05, 0.06, 0.04],
        'MOB_2': [0.08, 0.09, 0.07],
        'MOB_3': [0.12, 0.13, 0.11]
    })
    
    # Create mock prompt response
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
    
    # Mock data function
    def mock_data_func(sql):
        return test_data
    
    try:
        # Test simple mode (default)
        result = parser.parse_view_response("", mock_data_func, mock_prompt_response, mode="simple")
        print("✅ Simple模式解析成功")
        print("\n📋 Simple模式输出:")
        print("-" * 40)
        print(result)
        
        # Check if it's Markdown format
        if "📊 **查询结果**" in result and "```sql" in result and "📋 **分析报告**" in result:
            print("\n✅ Simple模式输出格式正确（Markdown格式）")
            return True
        else:
            print("\n❌ Simple模式输出格式不正确")
            return False
            
    except Exception as e:
        print(f"❌ Simple模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_mode_output():
    """测试Enhanced模式输出（chart-view格式）"""
    print("\n" + "="*60)
    print("🧪 测试2: Enhanced模式输出（chart-view格式）")
    print("="*60)
    
    # Create test data
    test_data = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['张三', '李四', '王五'],
        'amount': [1000, 2000, 1500]
    })
    
    # Create mock prompt response
    mock_prompt_response = SqlAction(
        sql="SELECT id, name, amount FROM customers LIMIT 3",
        thoughts={},
        display="",
        direct_response="",
        missing_info="",
        analysis_report={
            'summary': '客户数据查询结果',
            'key_findings': ['共有3个客户记录'],
            'insights': ['客户金额分布不均'],
            'recommendations': ['需要进一步分析客户价值']
        }
    )
    
    # Create parser and test
    parser = DbChatOutputParser()
    
    # Mock data function
    def mock_data_func(sql):
        return test_data
    
    try:
        # Test enhanced mode
        result = parser.parse_view_response("", mock_data_func, mock_prompt_response, mode="enhanced")
        print("✅ Enhanced模式解析成功")
        print("\n📋 Enhanced模式输出:")
        print("-" * 40)
        print(result)
        
        # Check if it's chart-view format
        if "<chart-view" in result and "content=" in result:
            print("\n✅ Enhanced模式输出格式正确（chart-view格式）")
            return True
        else:
            print("\n❌ Enhanced模式输出格式不正确")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_default_mode_behavior():
    """测试默认模式行为（应该是simple模式）"""
    print("\n" + "="*60)
    print("🧪 测试3: 默认模式行为（应该是simple模式）")
    print("="*60)
    
    # Create test data
    test_data = pd.DataFrame({
        'category': ['A', 'B', 'C'],
        'value': [100, 200, 150]
    })
    
    # Create mock prompt response
    mock_prompt_response = SqlAction(
        sql="SELECT category, value FROM test_table",
        thoughts={},
        display="",
        direct_response="",
        missing_info="",
        analysis_report={}
    )
    
    # Create parser and test
    parser = DbChatOutputParser()
    
    # Mock data function
    def mock_data_func(sql):
        return test_data
    
    try:
        # Test without specifying mode (should default to simple)
        result = parser.parse_view_response("", mock_data_func, mock_prompt_response)
        print("✅ 默认模式解析成功")
        print("\n📋 默认模式输出:")
        print("-" * 40)
        print(result)
        
        # Check if it's Markdown format (simple mode)
        if "📊 **查询结果**" in result and "```sql" in result and "<chart-view" not in result:
            print("\n✅ 默认模式正确使用Simple格式")
            return True
        else:
            print("\n❌ 默认模式未使用Simple格式")
            return False
            
    except Exception as e:
        print(f"❌ 默认模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mode_comparison():
    """对比两种模式的输出差异"""
    print("\n" + "="*60)
    print("🧪 测试4: 模式对比分析")
    print("="*60)
    
    # Create test data
    test_data = pd.DataFrame({
        'month': ['2025-01', '2025-02'],
        'revenue': [10000, 12000],
        'profit_rate': [0.15, 0.18]
    })
    
    # Create mock prompt response
    mock_prompt_response = SqlAction(
        sql="SELECT month, revenue, profit_rate FROM financial_data",
        thoughts={},
        display="",
        direct_response="",
        missing_info="",
        analysis_report={
            'summary': '财务数据分析',
            'key_findings': ['收入逐月增长', '利润率提升'],
            'insights': ['业务发展良好'],
            'recommendations': ['继续保持增长趋势']
        }
    )
    
    # Create parser
    parser = DbChatOutputParser()
    
    # Mock data function
    def mock_data_func(sql):
        return test_data
    
    try:
        # Test both modes
        simple_result = parser.parse_view_response("", mock_data_func, mock_prompt_response, mode="simple")
        enhanced_result = parser.parse_view_response("", mock_data_func, mock_prompt_response, mode="enhanced")
        
        print("📊 **Simple模式特征:**")
        print(f"- 输出长度: {len(simple_result)} 字符")
        print(f"- 包含Markdown表格: {'✅' if '|' in simple_result else '❌'}")
        print(f"- 包含SQL代码块: {'✅' if '```sql' in simple_result else '❌'}")
        print(f"- 包含分析报告: {'✅' if '📋 **分析报告**' in simple_result else '❌'}")
        print(f"- 用户友好格式: {'✅' if '📊' in simple_result else '❌'}")
        
        print("\n🔧 **Enhanced模式特征:**")
        print(f"- 输出长度: {len(enhanced_result)} 字符")
        print(f"- 包含chart-view标签: {'✅' if '<chart-view' in enhanced_result else '❌'}")
        print(f"- 包含JSON数据: {'✅' if 'content=' in enhanced_result else '❌'}")
        print(f"- 前端可渲染: {'✅' if '<chart-view' in enhanced_result else '❌'}")
        
        print("\n💡 **模式选择建议:**")
        print("- Simple模式: 适合直接阅读，用户体验更好")
        print("- Enhanced模式: 适合前端渲染，支持图表和交互功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 模式对比测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试双模式输出功能")
    print("="*60)
    
    # Run all tests
    test1_passed = test_simple_mode_output()
    test2_passed = test_enhanced_mode_output()
    test3_passed = test_default_mode_behavior()
    test4_passed = test_mode_comparison()
    
    print("\n" + "="*60)
    print("🎯 测试总结")
    print("="*60)
    print(f"   Simple模式测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"   Enhanced模式测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    print(f"   默认模式测试: {'✅ 通过' if test3_passed else '❌ 失败'}")
    print(f"   模式对比测试: {'✅ 通过' if test4_passed else '❌ 失败'}")
    
    if all([test1_passed, test2_passed, test3_passed, test4_passed]):
        print("\n🎉 所有测试通过! 双模式输出功能实现成功!")
        print("\n📋 功能特性:")
        print("   ✅ 默认使用Simple模式（Markdown格式）")
        print("   ✅ 支持Enhanced模式（chart-view格式）")
        print("   ✅ 保持向后兼容性")
        print("   ✅ 提升用户体验")
        return 0
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    exit(main()) 