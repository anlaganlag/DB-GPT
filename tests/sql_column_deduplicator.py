#!/usr/bin/env python3
"""
SQL Column Deduplicator - 解决DataFrame重复列名问题
自动检测和修复SQL查询中的重复列名，防止pandas orient='records'错误

使用方法:
1. 直接调用: python sql_column_deduplicator.py "SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id=t2.id"
2. 作为模块导入使用
"""

import re
import sys
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, Name


class SQLColumnDeduplicator:
    """SQL列名去重器"""
    
    def __init__(self):
        self.table_aliases = {}
        self.column_counts = {}
        
    def extract_table_aliases(self, sql):
        """提取SQL中的表别名"""
        aliases = {}
        
        # 简单的正则匹配表别名
        # 匹配 "table_name alias" 或 "table_name AS alias"
        pattern = r'\b(\w+)\s+(?:AS\s+)?(\w+)\b'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        
        for table, alias in matches:
            # 过滤掉SQL关键字
            if alias.upper() not in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'ON', 'AND', 'OR']:
                aliases[alias] = table
                
        return aliases
    
    def fix_duplicate_columns(self, sql):
        """修复SQL中的重复列名"""
        try:
            # 检查是否包含 SELECT *
            if re.search(r'SELECT\s+.*\*', sql, re.IGNORECASE):
                return self._fix_select_star(sql)
            else:
                return self._fix_explicit_columns(sql)
        except Exception as e:
            print(f"警告: SQL修复失败: {e}")
            return sql, []
    
    def _fix_select_star(self, sql):
        """修复包含SELECT *的SQL"""
        fixes_applied = []
        
        # 提取表别名
        aliases = self.extract_table_aliases(sql)
        
        if not aliases:
            # 没有别名的情况，无法自动修复
            return sql, ["检测到SELECT *但无法自动修复（缺少表别名）"]
        
        # 替换 SELECT * 为具体字段（这里需要根据实际表结构）
        # 由于无法获取实际表结构，我们采用保守策略：添加表前缀
        
        # 查找所有的 table.* 模式
        star_pattern = r'(\w+)\.\*'
        matches = re.findall(star_pattern, sql)
        
        if matches:
            # 如果有 table.* 的形式，给每个字段加上表前缀
            for alias in matches:
                # 这里我们无法知道具体字段，所以保持原样但记录警告
                fixes_applied.append(f"检测到{alias}.*，建议手动指定具体字段")
        
        return sql, fixes_applied
    
    def _fix_explicit_columns(self, sql):
        """修复明确指定列名的SQL"""
        fixes_applied = []
        
        # 使用sqlparse解析SQL
        try:
            parsed = sqlparse.parse(sql)[0]
            
            # 查找SELECT子句
            select_clause = None
            for token in parsed.tokens:
                if token.ttype is Keyword and token.value.upper() == 'SELECT':
                    continue
                if isinstance(token, IdentifierList):
                    select_clause = token
                    break
                elif isinstance(token, Identifier):
                    select_clause = token
                    break
            
            if select_clause:
                # 分析列名，添加别名避免重复
                modified_sql = self._add_column_aliases(sql, select_clause)
                if modified_sql != sql:
                    fixes_applied.append("为重复列名添加了别名")
                return modified_sql, fixes_applied
                
        except Exception as e:
            print(f"SQL解析失败: {e}")
        
        return sql, fixes_applied
    
    def _add_column_aliases(self, sql, select_clause):
        """为可能重复的列名添加别名"""
        # 这是一个简化的实现
        # 实际应用中需要更复杂的逻辑来检测和处理重复列名
        
        # 查找常见的可能重复的列名
        common_duplicates = ['id', 'name', 'created_at', 'updated_at', 'status']
        
        modified_sql = sql
        for col in common_duplicates:
            # 查找 table.column 模式
            pattern = rf'\b(\w+)\.({col})\b'
            matches = re.findall(pattern, sql, re.IGNORECASE)
            
            if len(matches) > 1:
                # 发现重复，添加别名
                for i, (table, column) in enumerate(matches):
                    old_ref = f"{table}.{column}"
                    new_ref = f"{table}.{column} AS {table}_{column}"
                    modified_sql = modified_sql.replace(old_ref, new_ref, 1)
        
        return modified_sql
    
    def validate_and_fix_sql(self, sql):
        """验证并修复SQL"""
        if not sql or not sql.strip():
            return sql, ["SQL为空"]
        
        # 基本安全检查
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'INSERT', 'UPDATE']
        sql_upper = sql.upper()
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper and not sql_upper.strip().startswith('SELECT'):
                return sql, [f"检测到危险操作: {keyword}"]
        
        # 修复重复列名
        fixed_sql, fixes = self.fix_duplicate_columns(sql)
        
        return fixed_sql, fixes


def main():
    """命令行工具入口"""
    if len(sys.argv) < 2:
        print("使用方法: python sql_column_deduplicator.py 'SQL查询语句'")
        print("示例: python sql_column_deduplicator.py 'SELECT * FROM table1 t1 JOIN table2 t2 ON t1.id=t2.id'")
        return
    
    sql = sys.argv[1]
    deduplicator = SQLColumnDeduplicator()
    
    print("原始SQL:")
    print(sql)
    print("\n" + "="*60)
    
    fixed_sql, fixes = deduplicator.validate_and_fix_sql(sql)
    
    print("修复后SQL:")
    print(fixed_sql)
    
    if fixes:
        print(f"\n应用的修复:")
        for fix in fixes:
            print(f"- {fix}")
    else:
        print("\n无需修复")


if __name__ == "__main__":
    main() 