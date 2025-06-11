#!/usr/bin/env python3
"""
测试SQL GROUP BY修复功能
Test SQL GROUP BY fix functionality
"""

import sys
import os

# 添加项目路径
sys.path.append('packages/dbgpt-app/src')

from dbgpt_app.scene.chat_db.auto_execute.sql_fixer import SQLFixer

def test_group_by_fixes():
    """测试GROUP BY相关的SQL修复"""
    fixer = SQLFixer()
    
    # 测试用例1：ONLY_FULL_GROUP_BY问题 - DATE_FORMAT with non-aggregated field
    test_sql_1 = """
    SELECT DATE_FORMAT(stat_date, '%Y-%m') AS stat_month, overdue_rate 
    FROM overdue_rate_stats 
    WHERE stat_date >= DATE_SUB(CURDATE(), INTERVAL 25 YEAR) 
    GROUP BY stat_month 
    ORDER BY stat_month LIMIT 50;
    """
    
    print("🔍 测试用例1: DATE_FORMAT with non-aggregated field")
    print(f"原始SQL: {test_sql_1.strip()}")
    
    fixed_sql_1, fixes_1 = fixer.fix_sql(test_sql_1)
    print(f"修复后SQL: {fixed_sql_1.strip()}")
    print(f"应用的修复: {fixes_1}")
    print("-" * 80)
    
    # 测试用例2：简单的GROUP BY问题
    test_sql_2 = """
    SELECT stat_month, overdue_rate 
    FROM overdue_rate_stats 
    GROUP BY stat_month 
    ORDER BY stat_month;
    """
    
    print("🔍 测试用例2: Simple GROUP BY issue")
    print(f"原始SQL: {test_sql_2.strip()}")
    
    fixed_sql_2, fixes_2 = fixer.fix_sql(test_sql_2)
    print(f"修复后SQL: {fixed_sql_2.strip()}")
    print(f"应用的修复: {fixes_2}")
    print("-" * 80)
    
    # 测试用例3：中文字段名的GROUP BY
    test_sql_3 = """
    SELECT 贷款月份, 逾期率 
    FROM overdue_rate_stats 
    GROUP BY 贷款月份;
    """
    
    print("🔍 测试用例3: Chinese field names in GROUP BY")
    print(f"原始SQL: {test_sql_3.strip()}")
    
    fixed_sql_3, fixes_3 = fixer.fix_sql(test_sql_3)
    print(f"修复后SQL: {fixed_sql_3.strip()}")
    print(f"应用的修复: {fixes_3}")
    print("-" * 80)

def test_mysql_connection():
    """测试MySQL连接和sql_mode"""
    import subprocess
    
    print("🔍 测试MySQL连接和sql_mode设置")
    
    try:
        # 检查sql_mode
        result = subprocess.run([
            'docker', 'exec', 'db-gpt-db-1', 'mysql', 
            '-u', 'root', '-paa123456', 
            '-e', 'SELECT @@sql_mode;'
        ], capture_output=True, text=True, check=True)
        
        print("当前sql_mode:")
        print(result.stdout)
        
        # 测试问题SQL
        problem_sql = """SELECT DATE_FORMAT(stat_date, '%Y-%m') AS stat_month, overdue_rate FROM overdue_rate_stats WHERE stat_date >= DATE_SUB(CURDATE(), INTERVAL 25 YEAR) GROUP BY stat_month ORDER BY stat_month LIMIT 5;"""
        
        print("测试问题SQL:")
        print(problem_sql)
        
        result = subprocess.run([
            'docker', 'exec', 'db-gpt-db-1', 'mysql', 
            '-u', 'root', '-paa123456', 'overdue_analysis',
            '-e', problem_sql
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SQL执行成功!")
            print(result.stdout)
        else:
            print("❌ SQL执行失败:")
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 SQL GROUP BY 修复功能测试")
    print("=" * 80)
    
    # 测试SQL修复功能
    test_group_by_fixes()
    
    print("\n" + "=" * 80)
    print("🔗 MySQL连接和sql_mode测试")
    print("=" * 80)
    
    # 测试MySQL连接
    test_mysql_connection()
    
    print("\n🎉 测试完成!") 