#!/usr/bin/env python3

def create_direct_fix():
    """创建直接修复脚本"""
    
    # 新的generate_input_values方法内容
    new_method_content = '''    @trace()
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
            
            # Convert to list and ensure we have strings
            table_infos = [str(info) for info in table_infos]
            
            # If we get empty results, try alternative methods
            if not table_infos:
                logger.warning("Direct table_simple_info returned empty, trying get_table_names")
                table_names = await blocking_func_to_async(
                    self._executor, self.database.get_table_names
                )
                table_names = list(table_names)
                logger.info(f"Retrieved {len(table_names)} table names: {table_names}")
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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't reset table_infos if we already have some data
            if not table_infos:
                logger.warning("No table info available, will try fallback methods")
                try:
                    # Try to get just table names as fallback
                    table_names = await blocking_func_to_async(
                        self._executor, self.database.get_table_names
                    )
                    table_names = list(table_names)
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
        return input_values'''
    
    # 创建Python脚本来直接替换
    script_content = f'''#!/usr/bin/env python3

import re

# 读取原文件
with open('/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py', 'r') as f:
    content = f.read()

# 新方法内容
new_method = """{new_method_content}"""

# 找到原方法的开始和结束位置
start_pattern = r'@trace\(\)\\s*async def generate_input_values\\(self\\) -> Dict:'
end_pattern = r'return input_values'

# 使用更精确的正则表达式匹配整个方法
pattern = r'(@trace\\(\\)\\s*async def generate_input_values\\(self\\) -> Dict:.*?return input_values)'

# 执行替换
new_content = re.sub(pattern, new_method.strip(), content, flags=re.DOTALL)

# 检查是否替换成功
if new_content != content:
    # 写回文件
    with open('/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py', 'w') as f:
        f.write(new_content)
    print("✅ 方法替换成功")
else:
    print("❌ 方法替换失败，可能是正则表达式不匹配")
    
    # 尝试手动查找和替换
    lines = content.split('\\n')
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if '@trace()' in line and 'async def generate_input_values' in lines[i+1] if i+1 < len(lines) else False:
            start_idx = i
        elif start_idx != -1 and 'return input_values' in line:
            end_idx = i
            break
    
    if start_idx != -1 and end_idx != -1:
        # 替换方法
        new_lines = lines[:start_idx] + new_method.split('\\n') + lines[end_idx+1:]
        new_content = '\\n'.join(new_lines)
        
        with open('/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py', 'w') as f:
            f.write(new_content)
        print("✅ 手动替换成功")
    else:
        print("❌ 无法找到方法边界")
'''
    
    with open('direct_fix.py', 'w') as f:
        f.write(script_content)
    
    import os
    os.chmod('direct_fix.py', 0o755)
    print("✅ 直接修复脚本已创建: direct_fix.py")

if __name__ == "__main__":
    create_direct_fix() 