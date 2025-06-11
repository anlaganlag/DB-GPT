#!/usr/bin/env python3
"""
测试DataFrame重复列修复功能
Test DataFrame duplicate column fix functionality
"""

import pandas as pd
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'packages/dbgpt-app/src'))

from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser, TimeAndReportFixer

def test_duplicate_column_dataframe():
    """测试DataFrame重复列处理"""
    print("🧪 测试DataFrame重复列处理...")
    
    # 创建包含重复列名的DataFrame
    data = {
        'loan_id': [1, 2, 3],
        'amount': [1000, 2000, 3000],
        'loan_id': [101, 102, 103],  # 重复列名
        'status': ['active', 'overdue', 'paid']
    }
    
    try:
        df = pd.DataFrame(data)
        print(f"原始DataFrame列名: {list(df.columns)}")
        
        # 创建parser实例
        parser = DbChatOutputParser()
        
        # 创建模拟的prompt_response
        class MockPromptResponse:
            def __init__(self):
                self.analysis_report = None
        
        mock_response = MockPromptResponse()
        
        # 测试格式化方法
        result = parser._format_result_for_display(df, mock_response)
        print("✅ DataFrame重复列处理成功")
        print(f"处理后的结果长度: {len(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ DataFrame重复列处理失败: {str(e)}")
        return False

def test_sql_duplicate_column_fix():
    """测试SQL重复列修复"""
    print("\n🧪 测试SQL重复列修复...")
    
    fixer = TimeAndReportFixer()
    
    test_sql = "SELECT ld.*, li.* FROM loan_details ld JOIN loan_info li ON ld.loan_id = li.loan_id WHERE ld.loan_month = '2023-05'"
    
    print(f"原始SQL: {test_sql}")
    
    fixed_sql = fixer.fix_sql_time_references(test_sql)
    
    print(f"修复后SQL: {fixed_sql}")
    
    # 检查是否修复了时间
    if "'2025-05'" in fixed_sql:
        print("✅ 时间修复成功: 2023-05 -> 2025-05")
    else:
        print("❌ 时间修复失败")
        return False
    
    # 检查是否修复了重复列
    if "ld.*" not in fixed_sql and "li.*" not in fixed_sql:
        print("✅ SQL重复列修复成功: 已替换 ld.*, li.*")
    else:
        print("❌ SQL重复列修复失败")
        return False
    
    return True

def test_error_scenario():
    """测试错误场景"""
    print("\n🧪 测试错误场景处理...")
    
    try:
        # 模拟pandas错误
        data = {'col1': [1, 2], 'col1': [3, 4]}  # 重复列名
        df = pd.DataFrame(data)
        
        # 尝试转换为records（这会失败）
        try:
            records = df.to_dict('records')
            print("❌ 预期的错误没有发生")
            return False
        except ValueError as e:
            if "must be unique" in str(e):
                print("✅ 成功捕获了重复列名错误")
                return True
            else:
                print(f"❌ 捕获了意外的错误: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 测试错误场景失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试DataFrame重复列修复功能\n")
    
    tests = [
        ("DataFrame重复列处理", test_duplicate_column_dataframe),
        ("SQL重复列修复", test_sql_duplicate_column_fix),
        ("错误场景处理", test_error_scenario)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        print(f"测试: {test_name}")
        print(f"{'='*50}")
        
        try:
            if test_func():
                print(f"✅ {test_name} - 通过")
                passed += 1
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"测试总结: {passed}/{total} 通过")
    print(f"{'='*50}")
    
    if passed == total:
        print("🎉 所有测试通过！DataFrame重复列修复功能正常工作。")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 