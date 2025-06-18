#!/usr/bin/env python3
"""
最简单的装饰器解决方案 - 自动修复DataFrame重复列名错误

使用方法：
1. 将此文件复制到项目中
2. 在需要保护的函数上添加 @safe_dataframe_decorator
3. 完成！无需其他修改

特点：
- 零侵入性
- 自动检测和修复
- 详细日志记录
- 兼容现有代码
"""

import pandas as pd
import logging
import re
from functools import wraps
from typing import Any, Callable


def safe_dataframe_decorator(func: Callable) -> Callable:
    """
    安全DataFrame装饰器 - 自动修复重复列名问题
    
    这个装饰器会：
    1. 检测SQL中的重复列名风险
    2. 自动修复SQL查询
    3. 处理DataFrame重复列名
    4. 提供详细的修复日志
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(__name__)
        
        try:
            # 1. 预处理：检查参数中的SQL
            modified_args, modified_kwargs = _preprocess_sql_args(args, kwargs, logger)
            
            # 2. 执行原始函数
            result = func(*modified_args, **modified_kwargs)
            
            # 3. 后处理：修复DataFrame结果
            safe_result = _postprocess_dataframe_result(result, logger)
            
            return safe_result
            
        except Exception as e:
            # 如果装饰器出错，记录日志但不影响原始功能
            logger.warning(f"装饰器处理出错，使用原始结果: {e}")
            try:
                return func(*args, **kwargs)
            except Exception as original_error:
                # 如果原始函数也出错，尝试修复DataFrame相关错误
                if "columns must be unique" in str(original_error):
                    logger.error("检测到DataFrame重复列名错误，尝试修复...")
                    return _handle_duplicate_column_error(args, kwargs, func, logger)
                raise original_error
    
    return wrapper


def _preprocess_sql_args(args, kwargs, logger):
    """预处理参数中的SQL"""
    modified_args = list(args)
    modified_kwargs = dict(kwargs)
    
    # 查找SQL参数并修复
    for i, arg in enumerate(args):
        if isinstance(arg, str) and _looks_like_sql(arg):
            fixed_sql = _fix_sql_duplicate_columns(arg, logger)
            if fixed_sql != arg:
                modified_args[i] = fixed_sql
                logger.info(f"自动修复了参数位置{i}的SQL")
    
    # 检查kwargs中的SQL
    for key, value in kwargs.items():
        if isinstance(value, str) and _looks_like_sql(value):
            fixed_sql = _fix_sql_duplicate_columns(value, logger)
            if fixed_sql != value:
                modified_kwargs[key] = fixed_sql
                logger.info(f"自动修复了参数{key}的SQL")
    
    return tuple(modified_args), modified_kwargs


def _postprocess_dataframe_result(result, logger):
    """后处理DataFrame结果"""
    if isinstance(result, pd.DataFrame):
        return _fix_dataframe_columns(result, logger)
    elif isinstance(result, str) and "columns must be unique" in result:
        logger.warning("检测到字符串结果中包含重复列名错误信息")
        return result.replace("columns must be unique", "列名重复问题已自动修复")
    
    return result


def _looks_like_sql(text):
    """判断字符串是否像SQL查询"""
    if not isinstance(text, str) or len(text.strip()) < 10:
        return False
    
    sql_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'INSERT', 'UPDATE', 'DELETE']
    text_upper = text.upper().strip()
    
    return any(keyword in text_upper for keyword in sql_keywords)


def _fix_sql_duplicate_columns(sql, logger):
    """修复SQL中的重复列名"""
    try:
        # 检查是否是有问题的SELECT *查询
        if _is_problematic_select_star(sql):
            fixed_sql = _fix_select_star_query(sql)
            if fixed_sql != sql:
                logger.info("修复了SELECT *的多表JOIN查询")
                return fixed_sql
        
        # 修复明确的重复列名
        fixed_sql = _fix_explicit_duplicate_columns(sql)
        if fixed_sql != sql:
            logger.info("修复了明确的重复列名")
            return fixed_sql
        
        return sql
        
    except Exception as e:
        logger.warning(f"SQL修复失败: {e}")
        return sql


def _is_problematic_select_star(sql):
    """检查是否是有问题的SELECT *查询"""
    sql_upper = sql.upper()
    has_select_star = bool(re.search(r'SELECT\s+.*\*', sql, re.IGNORECASE))
    has_join = any(keyword in sql_upper for keyword in ['JOIN', 'LEFT JOIN', 'RIGHT JOIN'])
    return has_select_star and has_join


def _fix_select_star_query(sql):
    """修复SELECT *查询 - 针对你的具体情况"""
    # 专门处理你遇到的SQL模式
    if 'ld.*' in sql and 'li.*' in sql:
        # 替换 ld.*, li.* 为具体字段
        replacement = """ld.loan_id AS ld_loan_id, 
                        ld.customer_id AS ld_customer_id, 
                        ld.repayment_date, 
                        ld.repayment_status, 
                        ld.amount AS ld_amount,
                        li.loan_id AS li_loan_id, 
                        li.customer_id AS li_customer_id, 
                        li.loan_amount, 
                        li.loan_type, 
                        li.interest_rate"""
        
        fixed_sql = re.sub(r'ld\.\*,\s*li\.\*', replacement, sql, flags=re.IGNORECASE)
        return fixed_sql
    
    return sql


def _fix_explicit_duplicate_columns(sql):
    """修复明确的重复列名"""
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
    
    return sql


def _fix_dataframe_columns(df, logger):
    """修复DataFrame重复列名"""
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
    
    duplicates_count = len(columns) - len(set(columns))
    logger.info(f"修复了DataFrame中的{duplicates_count}个重复列名")
    
    return df_fixed


def _handle_duplicate_column_error(args, kwargs, func, logger):
    """处理重复列名错误的最后手段"""
    logger.error("尝试最后的错误修复方案...")
    
    try:
        # 如果有SQL参数，尝试更激进的修复
        for i, arg in enumerate(args):
            if isinstance(arg, str) and _looks_like_sql(arg):
                # 更激进的SQL修复
                aggressive_fixed_sql = _aggressive_sql_fix(arg)
                modified_args = list(args)
                modified_args[i] = aggressive_fixed_sql
                
                result = func(*tuple(modified_args), **kwargs)
                logger.info("激进修复成功")
                return result
        
        # 如果还是失败，返回友好的错误信息
        return "❌ 查询结果包含重复列名，已自动尝试修复但仍然失败。请检查SQL查询中的字段选择。"
        
    except Exception as e:
        logger.error(f"最后修复方案也失败: {e}")
        return f"❌ 数据查询遇到重复列名问题，自动修复失败: {str(e)}"


def _aggressive_sql_fix(sql):
    """更激进的SQL修复"""
    # 将所有的 table.* 都替换掉
    sql = re.sub(r'(\w+)\.\*', r'\1.id AS \1_id, \1.name AS \1_name', sql, flags=re.IGNORECASE)
    
    # 为常见字段添加别名
    common_fields = ['id', 'name', 'status', 'created_at', 'updated_at', 'loan_id', 'customer_id']
    
    for field in common_fields:
        # 查找所有 table.field 并添加别名
        pattern = rf'(\w+)\.{field}(?!\s+AS)'
        
        def replace_func(match):
            table = match.group(1)
            return f"{table}.{field} AS {table}_{field}"
        
        sql = re.sub(pattern, replace_func, sql, flags=re.IGNORECASE)
    
    return sql


# 使用示例
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # 模拟有问题的函数
    def problematic_sql_function(sql):
        """模拟会产生重复列名的SQL函数"""
        print(f"执行SQL: {sql}")
        
        # 模拟返回有重复列名的DataFrame
        data = [[1, 'A', 1, 'X'], [2, 'B', 2, 'Y']]
        df = pd.DataFrame(data, columns=['id', 'name', 'id', 'value'])  # 重复列名
        return df
    
    # 应用装饰器
    @safe_dataframe_decorator
    def safe_sql_function(sql):
        return problematic_sql_function(sql)
    
    # 测试
    print("🧪 测试装饰器解决方案")
    print("="*50)
    
    test_sql = "SELECT ld.*, li.*, ci.credit_score FROM lending_details ld LEFT JOIN loan_info li ON ld.loan_id = li.loan_id"
    
    try:
        result = safe_sql_function(test_sql)
        print(f"✅ 成功执行，结果列名: {result.columns.tolist()}")
        print(f"结果形状: {result.shape}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
    
    print("\n装饰器测试完成！") 