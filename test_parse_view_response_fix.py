#!/usr/bin/env python3
"""
测试 parse_view_response 方法签名修复
"""

import sys
import os
sys.path.append('packages/dbgpt-app/src')
sys.path.append('packages/dbgpt-core/src')

from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser, SqlAction

def test_parse_view_response_signature():
    """测试 parse_view_response 方法签名是否正确"""
    
    print("🧪 测试 parse_view_response 方法签名...")
    
    # 创建解析器实例
    parser = DbChatOutputParser()
    
    # 测试方法签名
    import inspect
    sig = inspect.signature(parser.parse_view_response)
    params = list(sig.parameters.keys())
    
    print(f"📋 方法参数: {params}")
    
    # 期望的参数顺序: self, speak, data, prompt_response=None
    expected_params = ['speak', 'data', 'prompt_response']
    actual_params = params[1:]  # 排除 self
    
    if actual_params == expected_params:
        print("✅ 方法签名正确!")
        return True
    else:
        print(f"❌ 方法签名错误!")
        print(f"   期望: {expected_params}")
        print(f"   实际: {actual_params}")
        return False

def test_method_call():
    """测试方法调用是否正常"""
    
    print("\n🧪 测试方法调用...")
    
    try:
        parser = DbChatOutputParser()
        
        # 创建测试数据
        speak = "测试AI响应"
        data = lambda sql: None  # 模拟数据函数
        prompt_response = SqlAction(
            sql="SELECT 1",
            thoughts={"test": "思考"},
            display="table",
            direct_response="",
            analysis_report={}
        )
        
        # 测试调用
        result = parser.parse_view_response(speak, data, prompt_response)
        
        print("✅ 方法调用成功!")
        print(f"📤 返回结果类型: {type(result)}")
        return True
        
    except Exception as e:
        print(f"❌ 方法调用失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    
    print("🔧 测试 parse_view_response 方法修复")
    print("=" * 50)
    
    # 测试1: 方法签名
    test1_passed = test_parse_view_response_signature()
    
    # 测试2: 方法调用
    test2_passed = test_method_call()
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"   方法签名测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"   方法调用测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过! parse_view_response 方法修复成功!")
        return 0
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    exit(main()) 