#!/usr/bin/env python3

import os

def fix_chat_table_info():
    """直接修复容器内的chat.py文件"""
    
    print("🔧 修复chat.py文件中的table_simple_info问题...")
    
    # 新的generate_input_values方法
    new_method = '''    @trace()
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
        return input_values'''
    
    # 创建修复脚本
    script_content = f'''#!/bin/bash

echo "🔧 修复容器内chat.py文件..."

# 备份原文件
cp /app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py /app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py.backup

# 创建新的chat.py文件
cat > /app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/chat.py << 'EOF'
import logging
from typing import Dict, Type

from dbgpt import SystemApp
from dbgpt.agent.util.api_call import ApiCall
from dbgpt.util.executor_utils import blocking_func_to_async
from dbgpt.util.tracer import root_tracer, trace
from dbgpt_app.scene import BaseChat, ChatScene
from dbgpt_app.scene.base_chat import ChatParam
from dbgpt_app.scene.chat_db.auto_execute.config import ChatWithDBExecuteConfig
from dbgpt_app.scene.chat_db.auto_execute.sql_validator import SQLValidator
from dbgpt_serve.core.config import GPTsAppCommonConfig
from dbgpt_serve.datasource.manages import ConnectorManager

logger = logging.getLogger(__name__)


class ChatWithDbAutoExecute(BaseChat):
    chat_scene: str = ChatScene.ChatWithDbExecute.value()

    """Number of results to return from the query"""

    @classmethod
    def param_class(cls) -> Type[GPTsAppCommonConfig]:
        return ChatWithDBExecuteConfig

    def __init__(self, chat_param: ChatParam, system_app: SystemApp):
        """Chat Data Module Initialization
        Args:
           - chat_param: Dict
            - chat_session_id: (str) chat session_id
            - current_user_input: (str) current user input
            - model_name:(str) llm model name
            - select_param:(str) dbname
        """
        self.db_name = chat_param.select_param
        self.curr_config = chat_param.real_app_config(ChatWithDBExecuteConfig)
        super().__init__(chat_param=chat_param, system_app=system_app)
        if not self.db_name:
            raise ValueError(
                f"{{ChatScene.ChatWithDbExecute.value}} mode should chose db!"
            )
        with root_tracer.start_span(
            "ChatWithDbAutoExecute.get_connect", metadata={{"db_name": self.db_name}}
        ):
            local_db_manager = ConnectorManager.get_instance(self.system_app)
            self.database = local_db_manager.get_connector(self.db_name)
        
        # Initialize SQL validator
        self.sql_validator = SQLValidator(self.database)
        
        # Enhanced: Set both the validator and connector in the output parser
        output_parser = self.prompt_template.output_parser
        if hasattr(output_parser, 'set_sql_validator'):
            output_parser.set_sql_validator(self.sql_validator)
            logger.info("SQL validator set in output parser")
        
        if hasattr(output_parser, 'set_connector'):
            output_parser.set_connector(self.database)
            logger.info("Database connector set in output parser")
        
        # Log the enhancement status
        logger.info(f"Enhanced error handling initialized for database: {{self.db_name}}")
        
        self.api_call = ApiCall()

{new_method}

    def do_action(self, prompt_response):
        print(f"do_action:{{prompt_response}}")
        return self.database.run_to_df
EOF

echo "✅ chat.py文件修复完成"
echo "🔄 重启webserver以应用更改..."
'''
    
    with open('fix_chat_container.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('fix_chat_container.sh', 0o755)
    print("✅ 修复脚本已创建: fix_chat_container.sh")

if __name__ == "__main__":
    fix_chat_table_info() 