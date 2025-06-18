#!/bin/bash

echo "🔧 快速修复table_simple_info问题..."

# 创建新的generate_input_values方法
cat > /tmp/new_generate_method.py << 'EOF'
    @trace()
    async def generate_input_values(self) -> Dict:
        """
        generate input values
        """
        user_input = self.current_user_input.last_text
        
        # Enhanced: Force direct database query instead of relying on vector store
        logger.info("Forcing direct database table retrieval instead of vector store")
        
        table_infos = []
        
        try:
            # Get table info directly from database
            table_infos_raw = await blocking_func_to_async(
                self._executor, self.database.table_simple_info
            )
            table_infos = [str(info) for info in table_infos_raw]
            logger.info(f"Retrieved {len(table_infos)} tables directly from database")
            
            # If we get empty results, try alternative methods
            if not table_infos:
                logger.warning("Direct table_simple_info returned empty, trying get_table_names")
                table_names_raw = await blocking_func_to_async(
                    self._executor, self.database.get_table_names
                )
                table_names = list(table_names_raw)
                logger.info(f"Retrieved {len(table_names)} table names: {table_names}")
                if table_names:
                    # Create simple table info from table names
                    table_infos = [f"{name}(columns_not_detailed)" for name in table_names]
            
            logger.info(f"Final table_infos count: {len(table_infos)}")
            if table_infos:
                logger.info(f"Sample table info: {table_infos[0]}")
            
        except Exception as e:
            logger.error(f"Error retrieving table info: {e}")
            table_infos = []

        # Import RESPONSE_FORMAT_SIMPLE from prompt module
        from dbgpt_app.scene.chat_db.auto_execute.prompt import RESPONSE_FORMAT_SIMPLE
        
        input_values = {
            "user_input": user_input,
            "table_info": table_infos,
            "dialect": self.database.dialect,
            "db_name": self.database.get_current_db_name(),
            "top_k": 50,
            "display_type": ["Table", "Chart", "Text"],
            "response_format": RESPONSE_FORMAT_SIMPLE,
        }
        return input_values
EOF

# 使用Python脚本进行替换
python3 << 'EOF'
import re

# 读取原文件
with open('/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py', 'r') as f:
    content = f.read()

# 读取新方法
with open('/tmp/new_generate_method.py', 'r') as f:
    new_method = f.read()

# 找到方法的开始和结束
lines = content.split('\n')
start_idx = -1
end_idx = -1
indent_level = 0

for i, line in enumerate(lines):
    if '@trace()' in line:
        # 检查下一行是否是generate_input_values
        if i + 1 < len(lines) and 'async def generate_input_values' in lines[i + 1]:
            start_idx = i
            indent_level = len(line) - len(line.lstrip())
            break

if start_idx != -1:
    # 找到方法结束位置
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.strip() == 'return input_values':
            end_idx = i
            break

    if end_idx != -1:
        # 替换方法
        new_lines = lines[:start_idx] + new_method.split('\n') + lines[end_idx + 1:]
        new_content = '\n'.join(new_lines)
        
        # 写回文件
        with open('/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py', 'w') as f:
            f.write(new_content)
        print("✅ 方法替换成功")
    else:
        print("❌ 找不到方法结束位置")
else:
    print("❌ 找不到方法开始位置")
EOF

echo "✅ 修复完成"
