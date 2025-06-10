#!/usr/bin/env python3
"""
Enhanced SQL Fixer - 专门解决DataFrame重复列名问题
针对你遇到的具体错误："DataFrame columns must be unique for orient='records'"

这个工具可以：
1. 检测SQL中的重复列名
2. 自动为重复列名添加别名
3. 处理SELECT * 的情况
4. 提供详细的修复报告
"""

import re
import logging
from typing import Tuple, List, Dict


class EnhancedSQLFixer:
    """增强的SQL修复器，专门处理重复列名问题"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def fix_duplicate_columns_sql(self, sql: str) -> Tuple[str, List[str]]:
        """
        修复SQL中的重复列名问题
        
        Args:
            sql: 原始SQL查询
            
        Returns:
            tuple: (修复后的SQL, 应用的修复列表)
        """
        if not sql or not sql.strip():
            return sql, ["SQL为空"]
            
        fixes_applied = []
        fixed_sql = sql.strip()
        
        try:
            # 1. 处理SELECT * 的情况
            if self._has_select_star(fixed_sql):
                fixed_sql, star_fixes = self._fix_select_star_queries(fixed_sql)
                fixes_applied.extend(star_fixes)
            
            # 2. 处理明确的重复列名
            fixed_sql, column_fixes = self._fix_explicit_duplicate_columns(fixed_sql)
            fixes_applied.extend(column_fixes)
            
            # 3. 处理JOIN中的常见重复字段
            fixed_sql, join_fixes = self._fix_join_duplicate_columns(fixed_sql)
            fixes_applied.extend(join_fixes)
            
            return fixed_sql, fixes_applied
            
        except Exception as e:
            self.logger.error(f"SQL修复失败: {e}")
            return sql, [f"修复失败: {str(e)}"]
    
    def _has_select_star(self, sql: str) -> bool:
        """检查SQL是否包含SELECT *"""
        # 匹配 SELECT * 或 SELECT table.*
        pattern = r'SELECT\s+(?:\w+\.\*|\*)'
        return bool(re.search(pattern, sql, re.IGNORECASE))
    
    def _fix_select_star_queries(self, sql: str) -> Tuple[str, List[str]]:
        """修复包含SELECT *的查询"""
        fixes_applied = []
        
        # 检查是否是多表JOIN的SELECT *
        if self._is_multi_table_join(sql):
            # 这是最危险的情况，直接替换为明确的字段选择
            fixed_sql = self._replace_star_with_explicit_columns(sql)
            fixes_applied.append("将SELECT *替换为明确的字段选择以避免重复列名")
            return fixed_sql, fixes_applied
        
        return sql, fixes_applied
    
    def _is_multi_table_join(self, sql: str) -> bool:
        """检查是否是多表JOIN查询"""
        join_keywords = ['JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN']
        sql_upper = sql.upper()
        return any(keyword in sql_upper for keyword in join_keywords)
    
    def _replace_star_with_explicit_columns(self, sql: str) -> str:
        """将SELECT *替换为明确的字段选择"""
        # 提取表别名
        aliases = self._extract_table_aliases(sql)
        
        if not aliases:
            # 没有别名，无法安全替换
            return sql
        
        # 为每个表的常见字段添加别名
        explicit_columns = []
        common_fields = ['id', 'name', 'status', 'created_at', 'updated_at']
        
        for alias, table in aliases.items():
            for field in common_fields:
                explicit_columns.append(f"{alias}.{field} AS {alias}_{field}")
        
        if explicit_columns:
            # 替换SELECT *
            select_part = ", ".join(explicit_columns)
            fixed_sql = re.sub(
                r'SELECT\s+\*',
                f'SELECT {select_part}',
                sql,
                flags=re.IGNORECASE
            )
            return fixed_sql
        
        return sql
    
    def _extract_table_aliases(self, sql: str) -> Dict[str, str]:
        """提取SQL中的表别名"""
        aliases = {}
        
        # 匹配 FROM table alias 和 JOIN table alias
        patterns = [
            r'FROM\s+(\w+)\s+(?:AS\s+)?(\w+)',
            r'JOIN\s+(\w+)\s+(?:AS\s+)?(\w+)',
            r'LEFT\s+JOIN\s+(\w+)\s+(?:AS\s+)?(\w+)',
            r'RIGHT\s+JOIN\s+(\w+)\s+(?:AS\s+)?(\w+)',
            r'INNER\s+JOIN\s+(\w+)\s+(?:AS\s+)?(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for table, alias in matches:
                if alias.upper() not in ['ON', 'WHERE', 'AND', 'OR']:
                    aliases[alias] = table
        
        return aliases
    
    def _fix_explicit_duplicate_columns(self, sql: str) -> Tuple[str, List[str]]:
        """修复明确指定的重复列名"""
        fixes_applied = []
        
        # 查找可能重复的列名模式
        # 匹配 table.column 格式
        column_pattern = r'(\w+)\.(\w+)(?!\s+AS\s+\w+)'
        matches = re.findall(column_pattern, sql, re.IGNORECASE)
        
        # 统计列名出现次数
        column_counts = {}
        for table, column in matches:
            if column not in column_counts:
                column_counts[column] = []
            column_counts[column].append(table)
        
        # 找出重复的列名
        duplicates = {col: tables for col, tables in column_counts.items() if len(tables) > 1}
        
        if duplicates:
            fixed_sql = sql
            for column, tables in duplicates.items():
                for table in tables:
                    # 为重复的列名添加别名
                    old_pattern = f"{table}.{column}"
                    new_pattern = f"{table}.{column} AS {table}_{column}"
                    
                    # 只替换没有别名的情况
                    if f"{old_pattern} AS" not in fixed_sql:
                        fixed_sql = fixed_sql.replace(old_pattern, new_pattern)
            
            fixes_applied.append(f"为重复列名添加别名: {', '.join(duplicates.keys())}")
        
        return sql if not fixes_applied else fixed_sql, fixes_applied
    
    def _fix_join_duplicate_columns(self, sql: str) -> Tuple[str, List[str]]:
        """修复JOIN查询中的重复列名"""
        fixes_applied = []
        
        # 常见的JOIN中容易重复的字段
        common_join_duplicates = ['id', 'loan_id', 'customer_id', 'user_id', 'name', 'status']
        
        for field in common_join_duplicates:
            # 查找该字段在多个表中的使用
            pattern = rf'(\w+)\.{field}\b'
            matches = re.findall(pattern, sql, re.IGNORECASE)
            
            if len(set(matches)) > 1:  # 多个不同的表使用了同一个字段名
                # 为每个表的该字段添加别名
                for table in set(matches):
                    old_ref = f"{table}.{field}"
                    new_ref = f"{table}.{field} AS {table}_{field}"
                    
                    # 检查是否已经有别名
                    if f"{old_ref} AS" not in sql:
                        sql = sql.replace(old_ref, new_ref)
                        
                if f"{field}字段重复别名修复" not in fixes_applied:
                    fixes_applied.append(f"为{field}字段添加表前缀别名")
        
        return sql, fixes_applied
    
    def validate_sql_for_duplicates(self, sql: str) -> Tuple[bool, List[str]]:
        """验证SQL是否可能产生重复列名"""
        issues = []
        
        if self._has_select_star(sql) and self._is_multi_table_join(sql):
            issues.append("使用SELECT *进行多表JOIN可能导致重复列名")
        
        # 检查明确的重复列名
        column_pattern = r'(\w+)\.(\w+)'
        matches = re.findall(column_pattern, sql, re.IGNORECASE)
        
        column_counts = {}
        for table, column in matches:
            if column not in column_counts:
                column_counts[column] = []
            column_counts[column].append(table)
        
        duplicates = {col: tables for col, tables in column_counts.items() if len(tables) > 1}
        
        for column, tables in duplicates.items():
            issues.append(f"列名'{column}'在多个表中使用: {', '.join(tables)}")
        
        return len(issues) == 0, issues


def test_sql_fixer():
    """测试SQL修复器"""
    fixer = EnhancedSQLFixer()
    
    # 测试用例 - 你遇到的具体SQL
    test_sql = """
    SELECT ld.*, li.*, ci.credit_score, ci.age, ci.city, ci.education 
    FROM lending_details ld 
    LEFT JOIN loan_info li ON ld.loan_id = li.loan_id 
    LEFT JOIN customer_info ci ON li.customer_id = ci.id_number 
    WHERE ld.repayment_status = 'Overdue' 
    AND MONTH(ld.repayment_date) = 5 
    AND YEAR(ld.repayment_date) = YEAR(CURDATE()) 
    LIMIT 50;
    """
    
    print("原始SQL:")
    print(test_sql)
    print("\n" + "="*80)
    
    # 验证是否有问题
    is_valid, issues = fixer.validate_sql_for_duplicates(test_sql)
    print(f"SQL验证结果: {'通过' if is_valid else '有问题'}")
    if issues:
        print("发现的问题:")
        for issue in issues:
            print(f"  - {issue}")
    
    print("\n" + "="*80)
    
    # 修复SQL
    fixed_sql, fixes = fixer.fix_duplicate_columns_sql(test_sql)
    
    print("修复后SQL:")
    print(fixed_sql)
    
    if fixes:
        print(f"\n应用的修复:")
        for fix in fixes:
            print(f"  ✓ {fix}")
    else:
        print("\n无需修复")


if __name__ == "__main__":
    test_sql_fixer() 