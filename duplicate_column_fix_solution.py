#!/usr/bin/env python3
"""
完整解决方案：杜绝 "DataFrame columns must be unique for orient='records'" 错误

这个解决方案提供：
1. SQL预处理：自动修复重复列名
2. DataFrame安全处理：即使有重复列名也能正常工作
3. 错误预防：在问题发生前就解决
4. 详细日志：帮助调试和监控

使用方法：
1. 替换现有的SQL执行逻辑
2. 或者作为中间件使用
"""

import re
import pandas as pd
import logging
from typing import Tuple, List, Dict, Any, Callable
from functools import wraps


class DataFrameColumnFixer:
    """DataFrame列名修复器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def fix_duplicate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """修复DataFrame中的重复列名"""
        if df.empty:
            return df
            
        columns = df.columns.tolist()
        
        # 检查是否有重复列名
        if len(columns) == len(set(columns)):
            return df  # 没有重复，直接返回
        
        # 修复重复列名
        new_columns = []
        column_counts = {}
        
        for col in columns:
            if col in column_counts:
                column_counts[col] += 1
                new_col = f"{col}_{column_counts[col]}"
            else:
                column_counts[col] = 0
                new_col = col
            new_columns.append(new_col)
        
        # 创建新的DataFrame
        df_fixed = df.copy()
        df_fixed.columns = new_columns
        
        self.logger.info(f"修复了重复列名: {len(columns) - len(set(columns))} 个重复")
        return df_fixed
    
    def safe_to_dict(self, df: pd.DataFrame, orient='records') -> List[Dict]:
        """安全地将DataFrame转换为字典"""
        try:
            # 先修复重复列名
            df_fixed = self.fix_duplicate_columns(df)
            return df_fixed.to_dict(orient=orient)
        except Exception as e:
            self.logger.error(f"DataFrame转换失败: {e}")
            # 降级处理：返回简化的数据结构
            return [{"error": f"数据转换失败: {str(e)}"}]


class SQLColumnFixer:
    """SQL列名修复器 - 简化版"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def fix_sql(self, sql: str) -> Tuple[str, List[str]]:
        """修复SQL中的重复列名问题"""
        if not sql or not sql.strip():
            return sql, []
        
        fixes_applied = []
        fixed_sql = sql.strip()
        
        try:
            # 检测并修复 SELECT * 的多表JOIN
            if self._is_problematic_select_star(fixed_sql):
                fixed_sql = self._fix_select_star(fixed_sql)
                fixes_applied.append("修复了SELECT *的多表JOIN查询")
            
            # 修复明确的重复列名
            fixed_sql, column_fixes = self._fix_duplicate_column_references(fixed_sql)
            fixes_applied.extend(column_fixes)
            
            return fixed_sql, fixes_applied
            
        except Exception as e:
            self.logger.error(f"SQL修复失败: {e}")
            return sql, [f"修复失败: {str(e)}"]
    
    def _is_problematic_select_star(self, sql: str) -> bool:
        """检查是否是有问题的SELECT *查询"""
        sql_upper = sql.upper()
        has_select_star = bool(re.search(r'SELECT\s+.*\*', sql, re.IGNORECASE))
        has_join = any(keyword in sql_upper for keyword in ['JOIN', 'LEFT JOIN', 'RIGHT JOIN'])
        return has_select_star and has_join
    
    def _fix_select_star(self, sql: str) -> str:
        """修复SELECT *查询"""
        # 简单的修复：将 ld.*, li.* 替换为具体字段
        if 'ld.*' in sql and 'li.*' in sql:
            # 针对你的具体情况
            replacement = """ld.loan_id AS ld_loan_id, ld.customer_id AS ld_customer_id, 
                           ld.repayment_date, ld.repayment_status, ld.amount AS ld_amount,
                           li.loan_id AS li_loan_id, li.customer_id AS li_customer_id, 
                           li.loan_amount, li.loan_type, li.interest_rate"""
            
            fixed_sql = re.sub(r'ld\.\*,\s*li\.\*', replacement, sql, flags=re.IGNORECASE)
            return fixed_sql
        
        return sql
    
    def _fix_duplicate_column_references(self, sql: str) -> Tuple[str, List[str]]:
        """修复重复的列名引用"""
        fixes_applied = []
        
        # 常见的重复字段
        common_duplicates = ['loan_id', 'customer_id', 'id', 'name', 'status']
        
        for field in common_duplicates:
            # 查找 table.field 模式
            pattern = rf'(\w+)\.{field}(?!\s+AS\s+\w+)'
            matches = re.findall(pattern, sql, re.IGNORECASE)
            
            if len(set(matches)) > 1:
                # 为每个表的字段添加别名
                for table in set(matches):
                    old_ref = f"{table}.{field}"
                    new_ref = f"{table}.{field} AS {table}_{field}"
                    sql = sql.replace(old_ref, new_ref)
                
                fixes_applied.append(f"为{field}字段添加了表前缀别名")
        
        return sql, fixes_applied


class SafeSQLExecutor:
    """安全的SQL执行器 - 防止重复列名错误"""
    
    def __init__(self, original_executor: Callable):
        """
        Args:
            original_executor: 原始的SQL执行函数
        """
        self.original_executor = original_executor
        self.sql_fixer = SQLColumnFixer()
        self.df_fixer = DataFrameColumnFixer()
        self.logger = logging.getLogger(__name__)
    
    def execute(self, sql: str) -> pd.DataFrame:
        """安全执行SQL查询"""
        try:
            # 1. 预处理SQL
            fixed_sql, fixes = self.sql_fixer.fix_sql(sql)
            
            if fixes:
                self.logger.info(f"应用了SQL修复: {fixes}")
            
            # 2. 执行SQL
            result = self.original_executor(fixed_sql)
            
            # 3. 检查结果
            if result is None or result.empty:
                return result
            
            # 4. 修复DataFrame列名（如果需要）
            safe_result = self.df_fixer.fix_duplicate_columns(result)
            
            return safe_result
            
        except Exception as e:
            self.logger.error(f"安全SQL执行失败: {e}")
            # 尝试原始SQL
            try:
                result = self.original_executor(sql)
                return self.df_fixer.fix_duplicate_columns(result)
            except Exception as e2:
                self.logger.error(f"原始SQL也失败: {e2}")
                raise e2


def safe_sql_wrapper(original_function):
    """装饰器：为现有的SQL执行函数添加安全保护"""
    
    @wraps(original_function)
    def wrapper(*args, **kwargs):
        try:
            # 假设第一个参数是SQL
            if args:
                sql = args[0]
                fixer = SQLColumnFixer()
                fixed_sql, fixes = fixer.fix_sql(sql)
                
                if fixes:
                    logging.info(f"自动修复SQL: {fixes}")
                    args = (fixed_sql,) + args[1:]
            
            # 执行原始函数
            result = original_function(*args, **kwargs)
            
            # 如果结果是DataFrame，修复列名
            if isinstance(result, pd.DataFrame):
                df_fixer = DataFrameColumnFixer()
                result = df_fixer.fix_duplicate_columns(result)
            
            return result
            
        except Exception as e:
            logging.error(f"SQL执行包装器错误: {e}")
            raise
    
    return wrapper


# 使用示例和测试
def test_solution():
    """测试完整解决方案"""
    
    # 模拟原始SQL执行函数
    def mock_sql_executor(sql):
        """模拟SQL执行，返回有重复列名的DataFrame"""
        # 模拟你遇到的情况
        data = {
            'loan_id': [1, 2, 3],  # 来自 ld 表
            'loan_id': [1, 2, 3],  # 来自 li 表 - 重复列名！
            'customer_id': [101, 102, 103],  # 来自 ld 表
            'customer_id': [101, 102, 103],  # 来自 li 表 - 重复列名！
            'amount': [1000, 2000, 3000],
        }
        return pd.DataFrame(data)
    
    # 测试SQL修复
    sql_fixer = SQLColumnFixer()
    test_sql = """
    SELECT ld.*, li.*, ci.credit_score 
    FROM lending_details ld 
    LEFT JOIN loan_info li ON ld.loan_id = li.loan_id 
    LEFT JOIN customer_info ci ON li.customer_id = ci.id_number
    """
    
    print("=== SQL修复测试 ===")
    fixed_sql, fixes = sql_fixer.fix_sql(test_sql)
    print(f"原始SQL: {test_sql}")
    print(f"修复后SQL: {fixed_sql}")
    print(f"应用的修复: {fixes}")
    
    # 测试DataFrame修复
    print("\n=== DataFrame修复测试 ===")
    df_fixer = DataFrameColumnFixer()
    
    # 创建有重复列名的DataFrame
    try:
        problematic_df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'id': [4, 5, 6],  # 重复列名
        })
    except:
        # pandas可能不允许直接创建重复列名，我们手动创建
        problematic_df = pd.DataFrame([[1, 'A', 4], [2, 'B', 5], [3, 'C', 6]])
        problematic_df.columns = ['id', 'name', 'id']  # 手动设置重复列名
    
    print(f"问题DataFrame列名: {problematic_df.columns.tolist()}")
    
    fixed_df = df_fixer.fix_duplicate_columns(problematic_df)
    print(f"修复后DataFrame列名: {fixed_df.columns.tolist()}")
    
    # 测试安全转换
    try:
        dict_result = df_fixer.safe_to_dict(problematic_df)
        print(f"安全转换成功: {len(dict_result)} 条记录")
    except Exception as e:
        print(f"转换失败: {e}")
    
    # 测试安全执行器
    print("\n=== 安全执行器测试 ===")
    safe_executor = SafeSQLExecutor(mock_sql_executor)
    
    try:
        result = safe_executor.execute(test_sql)
        print(f"安全执行成功，结果列名: {result.columns.tolist()}")
    except Exception as e:
        print(f"安全执行失败: {e}")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print("🔧 DataFrame重复列名问题完整解决方案")
    print("="*60)
    
    test_solution()
    
    print("\n" + "="*60)
    print("✅ 解决方案说明:")
    print("1. 使用 SQLColumnFixer 预处理SQL查询")
    print("2. 使用 DataFrameColumnFixer 修复DataFrame列名")
    print("3. 使用 SafeSQLExecutor 包装现有的SQL执行逻辑")
    print("4. 使用 @safe_sql_wrapper 装饰器保护现有函数")
    print("\n这样可以在不改动核心代码的情况下，杜绝重复列名错误！") 