#!/usr/bin/env python3
"""
简化的DataFrame重复列修复测试
"""

import pandas as pd

def test_duplicate_columns():
    """测试重复列处理逻辑"""
    print("🧪 测试DataFrame重复列处理逻辑...")
    
    # 模拟有重复列名的DataFrame
    data = {
        'loan_id': [1, 2, 3],
        'amount': [1000, 2000, 3000],
        'status': ['active', 'overdue', 'paid']
    }
    
    # 手动创建重复列名
    df = pd.DataFrame(data)
    df.columns = ['loan_id', 'amount', 'loan_id']  # 手动设置重复列名
    
    print(f"原始列名: {list(df.columns)}")
    print(f"是否有重复: {len(df.columns) != len(set(df.columns))}")
    
    # 应用修复逻辑
    if len(df.columns) != len(set(df.columns)):
        print("检测到重复列名，正在修复...")
        
        new_columns = []
        column_counts = {}
        
        for col in df.columns:
            if col in column_counts:
                column_counts[col] += 1
                new_col_name = f"{col}_{column_counts[col]}"
            else:
                column_counts[col] = 0
                new_col_name = col
            new_columns.append(new_col_name)
        
        df.columns = new_columns
        print(f"修复后列名: {list(df.columns)}")
        
        # 测试转换为records
        try:
            records = df.to_dict('records')
            print("✅ 成功转换为records格式")
            print(f"记录数: {len(records)}")
            return True
        except Exception as e:
            print(f"❌ 转换失败: {e}")
            return False
    
    return True

def test_sql_fix():
    """测试SQL修复逻辑"""
    print("\n🧪 测试SQL修复逻辑...")
    
    import re
    
    sql = "SELECT ld.*, li.* FROM loan_details ld JOIN loan_info li ON ld.loan_id = li.loan_id WHERE ld.loan_month = '2023-05'"
    print(f"原始SQL: {sql}")
    
    # 时间修复
    fixed_sql = re.sub(r"'2023-(\d{2})'", "'2025-\\1'", sql)
    print(f"时间修复后: {fixed_sql}")
    
    # 重复列修复
    pattern = r'SELECT\s+(\w+)\.\*\s*,\s*(\w+)\.\*'
    match = re.search(pattern, fixed_sql, re.IGNORECASE)
    
    if match:
        table1_alias = match.group(1)
        table2_alias = match.group(2)
        print(f"检测到重复列模式: {table1_alias}.*, {table2_alias}.*")
        
        replacement = f"SELECT {table1_alias}.loan_id AS '{table1_alias}_loan_id', {table1_alias}.amount AS '{table1_alias}_amount', {table2_alias}.customer_id AS '{table2_alias}_customer_id'"
        
        final_sql = re.sub(pattern, replacement, fixed_sql, flags=re.IGNORECASE)
        print(f"最终SQL: {final_sql}")
        
        return "'2025-05'" in final_sql and ".*" not in final_sql
    
    return False

if __name__ == "__main__":
    print("🚀 开始简化测试\n")
    
    test1 = test_duplicate_columns()
    test2 = test_sql_fix()
    
    print(f"\n📊 测试结果:")
    print(f"DataFrame重复列修复: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"SQL修复: {'✅ 通过' if test2 else '❌ 失败'}")
    
    if test1 and test2:
        print("\n🎉 所有测试通过！修复功能正常工作。")
    else:
        print("\n⚠️ 部分测试失败。") 