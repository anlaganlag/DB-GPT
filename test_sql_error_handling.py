#!/usr/bin/env python3
"""
Test script for SQL error handling and fixing
测试SQL错误处理和修复功能的脚本
"""

import sys
import os
sys.path.append('packages/dbgpt-app/src')

from dbgpt_app.scene.chat_db.auto_execute.sql_fixer import create_sql_fixer

def test_sql_fixer():
    """Test the SQL fixer with common problematic SQL patterns"""
    
    fixer = create_sql_fixer()
    
    # Test case 1: CTE alias mismatch (the exact issue we found)
    problematic_sql_1 = """
    WITH monthly_overdue AS (
        SELECT 
            stat_date AS '统计日期',
            loan_month AS '贷款月份',
            mob AS 'Month of Book',
            total_loans AS '总贷款数',
            overdue_rate AS '逾期率'
        FROM overdue_rate_stats
        WHERE loan_month IN ('2023-04', '2023-05', '2023-06', '2023-07')
    )
    SELECT 
        m.loan_month,
        m.overdue_rate
    FROM monthly_overdue m
    ORDER BY m.loan_month ASC
    LIMIT 50;
    """
    
    print("🧪 测试案例 1: CTE别名不匹配问题")
    print("原始SQL:")
    print(problematic_sql_1)
    
    fixed_sql_1, fixes_1 = fixer.fix_sql(problematic_sql_1)
    print("\n修复后的SQL:")
    print(fixed_sql_1)
    print(f"\n应用的修复: {fixes_1}")
    print("\n" + "="*80 + "\n")
    
    # Test case 2: Chinese aliases without quotes
    problematic_sql_2 = """
    SELECT 
        loan_month AS 贷款月份,
        overdue_rate AS 逾期率
    FROM overdue_rate_stats
    GROUP BY 贷款月份
    ORDER BY 贷款月份;
    """
    
    print("🧪 测试案例 2: 中文别名未加引号")
    print("原始SQL:")
    print(problematic_sql_2)
    
    fixed_sql_2, fixes_2 = fixer.fix_sql(problematic_sql_2)
    print("\n修复后的SQL:")
    print(fixed_sql_2)
    print(f"\n应用的修复: {fixes_2}")
    print("\n" + "="*80 + "\n")

def test_error_formatting():
    """Test error message formatting"""
    
    # Import the error formatting function
    from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser
    
    parser = DbChatOutputParser()
    
    # Test different types of SQL errors
    test_errors = [
        "Unknown column 'm.loan_month' in 'field list'",
        "Table 'test.nonexistent_table' doesn't exist",
        "You have an error in your SQL syntax",
        "Column 'amount' in field list is ambiguous",
    ]
    
    print("🧪 测试错误信息格式化:")
    for error_msg in test_errors:
        # Create a mock exception
        class MockError(Exception):
            def __str__(self):
                return error_msg
        
        mock_error = MockError()
        formatted = parser.format_sql_error_for_user(mock_error)
        print(f"\n原始错误: {error_msg}")
        print(f"格式化后: {formatted}")
    
    print("\n" + "="*80 + "\n")

def test_sql_validation():
    """Test SQL validation"""
    
    from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser
    
    parser = DbChatOutputParser()
    
    test_sqls = [
        ("SELECT * FROM users", True, "正常的SELECT查询"),
        ("DROP TABLE users", False, "危险的DROP操作"),
        ("", False, "空SQL"),
        ("WITH cte AS (SELECT * FROM users) SELECT * FROM cte", True, "CTE查询"),
        ("INSERT INTO users VALUES (1, 'test')", False, "INSERT操作"),
    ]
    
    print("🧪 测试SQL验证:")
    for sql, expected_valid, description in test_sqls:
        is_valid, error_msg = parser.validate_sql_basic(sql)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"{status} {description}: {is_valid} ({error_msg if error_msg else 'OK'})")
    
    print("\n" + "="*80 + "\n")

def main():
    """Run all tests"""
    print("🚀 开始测试SQL错误处理和修复功能\n")
    
    try:
        test_sql_fixer()
        test_error_formatting()
        test_sql_validation()
        
        print("✅ 所有测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 