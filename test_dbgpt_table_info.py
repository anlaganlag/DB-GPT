#!/usr/bin/env python3

import sys
import os
import asyncio
sys.path.append('/app')

from dbgpt import SystemApp
from dbgpt_serve.datasource.manages.connector_manager import ConnectorManager
from dbgpt.util.executor_utils import blocking_func_to_async
import concurrent.futures

def test_dbgpt_table_info():
    """测试DB-GPT内部的table_simple_info调用"""
    
    print("🔍 测试DB-GPT内部的table_simple_info调用...")
    
    try:
        # 初始化系统应用
        print("🚀 初始化SystemApp...")
        system_app = SystemApp()
        
        # 手动注册ConnectorManager
        print("📡 注册ConnectorManager...")
        system_app.register(ConnectorManager)
        
        # 获取连接管理器
        print("🔗 获取ConnectorManager实例...")
        db_manager = ConnectorManager.get_instance(system_app)
        
        # 获取orange数据源连接器
        print("🔗 获取orange数据源连接器...")
        connector = db_manager.get_connector("orange")
        
        if not connector:
            print("❌ 无法获取orange数据源连接器")
            return False
            
        print(f"✅ 连接器类型: {type(connector).__name__}")
        print(f"✅ 数据库类型: {connector.db_type}")
        print(f"✅ 数据库方言: {connector.dialect}")
        
        # 测试基本连接
        print("\n🧪 测试基本连接...")
        try:
            current_db = connector.get_current_db_name()
            print(f"✅ 当前数据库: {current_db}")
        except Exception as e:
            print(f"❌ 获取当前数据库名失败: {e}")
            
        # 测试获取表名
        print("\n📋 测试获取表名...")
        try:
            table_names = list(connector.get_table_names())
            print(f"✅ 表数量: {len(table_names)}")
            print(f"✅ 前10个表: {table_names[:10]}")
        except Exception as e:
            print(f"❌ 获取表名失败: {e}")
            
        # 核心测试：table_simple_info
        print("\n🎯 测试table_simple_info方法...")
        try:
            simple_info = list(connector.table_simple_info())
            
            print(f"✅ table_simple_info返回数量: {len(simple_info)}")
            
            if simple_info:
                print("✅ 前5个表结构信息:")
                for i, info in enumerate(simple_info[:5]):
                    print(f"  {i+1}. {info}")
            else:
                print("❌ table_simple_info返回空列表!")
                
        except Exception as e:
            print(f"❌ table_simple_info方法失败: {e}")
            import traceback
            traceback.print_exc()
            
        # 测试异步调用（模拟chat.py中的调用方式）
        print("\n🔄 测试异步调用table_simple_info...")
        try:
            async def test_async():
                executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                table_infos = await blocking_func_to_async(
                    executor, connector.table_simple_info
                )
                return list(table_infos)
            
            # 运行异步测试
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async_result = loop.run_until_complete(test_async())
            loop.close()
            
            print(f"✅ 异步调用返回数量: {len(async_result)}")
            if async_result:
                print("✅ 异步调用前3个结果:")
                for i, info in enumerate(async_result[:3]):
                    print(f"  {i+1}. {info}")
            else:
                print("❌ 异步调用返回空列表!")
                
        except Exception as e:
            print(f"❌ 异步调用失败: {e}")
            import traceback
            traceback.print_exc()
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_dbgpt_table_info() 