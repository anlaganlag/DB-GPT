#!/usr/bin/env python3

def create_simple_fix():
    """创建简单的修复脚本"""
    
    script_content = '''#!/bin/bash

echo "🔧 简单修复chat.py文件的generate_input_values方法..."

# 备份原文件
cp /app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py /app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py.backup2

# 使用sed替换generate_input_values方法
cat > /tmp/new_method.py << 'EOF'
    @trace()
    async def generate_input_values(self) -> Dict:
        """
        generate input values
        """
        user_input = self.current_user_input.last_text
        
        # Enhanced: Force direct database query instead of relying on vector store
        logger.info("Forcing direct database table retrieval instead of vector store")
        
        table_infos = []
        table_count_info = "❌ 无法获取表信息"
        
        try:
            # Get table info directly from database
            table_infos = await blocking_func_to_async(
                self._executor, self.database.table_simple_info
            )
            logger.info(f"Retrieved {len(table_infos)} tables directly from database")
            
            # If we get empty results, try alternative methods
            if not table_infos:
                logger.warning("Direct table_simple_info returned empty, trying get_table_names")
                table_names = await blocking_func_to_async(
                    self._executor, self.database.get_table_names
                )
                logger.info(f"Retrieved {len(table_names)} table names: {list(table_names)}")
                if table_names:
                    # Create simple table info from table names
                    table_infos = [f"{name}(columns_not_detailed)" for name in table_names]
            
            logger.info(f"Final table_infos count: {len(table_infos)}")
            if table_infos:
                logger.info(f"Sample table info: {table_infos[0]}")
                # Only create table count info if we have valid table_infos
                table_count_info = f"📊 数据库表统计信息：数据库名={self.database.get_current_db_name()}, 表总数={len(table_infos)}个表, 表名列表=[{', '.join([info.split('(')[0] for info in table_infos])}]"
            
        except Exception as e:
            logger.error(f"Error retrieving table info: {e}")
            # Don't reset table_infos if we already have some data
            if not table_infos:
                logger.warning("No table info available, will try fallback methods")
                try:
                    # Try to get just table names as fallback
                    table_names = await blocking_func_to_async(
                        self._executor, self.database.get_table_names
                    )
                    if table_names:
                        table_infos = [f"{name}(structure_unavailable)" for name in table_names]
                        table_count_info = f"📊 数据库表统计信息：数据库名={self.database.get_current_db_name()}, 表总数={len(table_infos)}个表, 表名列表=[{', '.join(table_names)}]"
                        logger.info(f"Fallback: Retrieved {len(table_names)} table names")
                except Exception as fallback_error:
                    logger.error(f"Fallback method also failed: {fallback_error}")
                    table_count_info = "❌ 无法获取表信息"

        # Import RESPONSE_FORMAT_SIMPLE from prompt module
        from dbgpt_app.scene.chat_db.auto_execute.prompt import RESPONSE_FORMAT_SIMPLE
        import json
        
        # Add the count information as the last item in table_infos
        if table_infos:
            table_infos_with_stats = table_infos + [table_count_info]
        else:
            table_infos_with_stats = [table_count_info]
        
        # Define available display types
        display_types = ["Table", "Chart", "Text"]
        
        input_values = {
            "user_input": user_input,
            "table_info": table_infos_with_stats,
            "dialect": self.database.dialect,
            "db_name": self.database.get_current_db_name(),
            "top_k": 50,  # Default limit for query results
            "display_type": display_types,  # Available display methods
            "response_format": RESPONSE_FORMAT_SIMPLE,  # JSON response format
        }
        return input_values
EOF

# 创建Python脚本来替换方法
cat > /tmp/replace_method.py << 'EOF'
import re

# 读取原文件
with open('/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py', 'r') as f:
    content = f.read()

# 读取新方法
with open('/tmp/new_method.py', 'r') as f:
    new_method = f.read()

# 使用正则表达式替换generate_input_values方法
pattern = r'(@trace\(\)\s+async def generate_input_values.*?return input_values)'
replacement = new_method.strip()

# 执行替换
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 写回文件
with open('/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py', 'w') as f:
    f.write(new_content)

print("✅ 方法替换完成")
EOF

# 执行替换
python3 /tmp/replace_method.py

echo "✅ chat.py文件修复完成"
'''
    
    with open('simple_fix_chat.sh', 'w') as f:
        f.write(script_content)
    
    import os
    os.chmod('simple_fix_chat.sh', 0o755)
    print("✅ 简单修复脚本已创建: simple_fix_chat.sh")

if __name__ == "__main__":
    create_simple_fix() 