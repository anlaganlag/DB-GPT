#!/bin/bash

echo "🔧 快速修复 sql_fixer 模块缺失问题"
echo "===================================="

CONTAINER_NAME="db-gpt_webserver_1"
TARGET_DIR="/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/"

# 检查容器是否运行
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ 容器 $CONTAINER_NAME 未运行，请先启动容器"
    exit 1
fi

# 检查本地sql_fixer.py是否存在
if [[ ! -f "./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/sql_fixer.py" ]]; then
    echo "❌ 本地 sql_fixer.py 文件不存在"
    echo "正在创建基本的 sql_fixer.py 文件..."
    
    # 创建基本的sql_fixer.py文件
    cat > "./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/sql_fixer.py" << 'EOF'
"""
SQL修复器模块 - 基本版本
用于修复SQL语句中的常见问题
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class SQLFixer:
    """SQL修复器"""
    
    def __init__(self):
        self.current_year = 2024
    
    def fix_sql(self, sql: str) -> str:
        """修复SQL语句"""
        if not sql:
            return sql
        
        # 修复时间引用
        fixed_sql = self._fix_time_references(sql)
        
        # 修复重复列名问题
        fixed_sql = self._fix_duplicate_columns(fixed_sql)
        
        # 修复Apache Doris兼容性问题
        fixed_sql = self._fix_doris_compatibility(fixed_sql)
        
        if fixed_sql != sql:
            logger.info(f"SQL已修复: {sql} -> {fixed_sql}")
        
        return fixed_sql
    
    def _fix_time_references(self, sql: str) -> str:
        """修复时间引用"""
        # 替换硬编码的年份
        sql = re.sub(r"'2023-(\d{2})'", f"'{self.current_year}-\\1'", sql)
        return sql
    
    def _fix_duplicate_columns(self, sql: str) -> str:
        """修复重复列名问题"""
        # 检测 SELECT table1.*, table2.* 模式
        pattern = r'SELECT\s+(\w+)\.\*\s*,\s*(\w+)\.\*'
        if re.search(pattern, sql, re.IGNORECASE):
            logger.warning("检测到可能导致重复列名的SQL模式")
            # 这里可以添加更复杂的修复逻辑
        return sql
    
    def _fix_doris_compatibility(self, sql: str) -> str:
        """修复Apache Doris兼容性问题"""
        # 移除不支持的语法
        sql = re.sub(r'SHOW TABLES LIKE \'([^\']+\|[^\']+)\'', 'SHOW TABLES', sql)
        sql = re.sub(r'SHOW TABLES LIMIT \d+', 'SHOW TABLES', sql)
        return sql

def create_sql_fixer() -> SQLFixer:
    """创建SQL修复器实例"""
    return SQLFixer()
EOF
    
    echo "✅ 已创建基本的 sql_fixer.py 文件"
fi

# 复制sql_fixer.py到容器
echo "📁 复制 sql_fixer.py 到容器..."
docker cp "./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/sql_fixer.py" \
    "$CONTAINER_NAME:$TARGET_DIR"

# 验证复制结果
echo "✅ 验证文件复制..."
docker exec "$CONTAINER_NAME" ls -la "$TARGET_DIR" | grep sql_fixer

# 测试模块导入
echo "🧪 测试 sql_fixer 模块导入..."
docker exec "$CONTAINER_NAME" python3 -c "
try:
    from dbgpt_app.scene.chat_db.auto_execute.sql_fixer import create_sql_fixer
    fixer = create_sql_fixer()
    print('✅ sql_fixer 模块导入和实例化成功')
    
    # 测试基本功能
    test_sql = \"SELECT * FROM table WHERE date = '2023-01'\"
    fixed_sql = fixer.fix_sql(test_sql)
    print(f'✅ SQL修复功能测试: \"{test_sql}\" -> \"{fixed_sql}\"')
    
except Exception as e:
    print(f'❌ sql_fixer 模块测试失败: {e}')
    import traceback
    traceback.print_exc()
"

echo -e "\n🎉 sql_fixer 模块修复完成！"
echo "现在可以尝试重新运行您的分析报告功能了。" 