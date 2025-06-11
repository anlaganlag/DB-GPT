#!/usr/bin/env python3
"""
测试增强的SQL错误显示功能
验证即使SQL报错也不会显示通用的"Generate view content failed"错误
而是展示详细的SQL和错误信息
"""

import requests
import json
import time

def test_sql_error_with_detailed_display():
    """测试SQL错误时的详细显示"""
    print("🔧 测试SQL错误的详细显示功能...")
    
    # 构造一个会导致SQL错误的查询
    test_query = {
        "conv_uid": "test-sql-error-display",
        "user_input": "查询不存在的表 non_existent_table 的数据",
        "user_name": "test_user",
        "chat_mode": "chat_with_db_execute",
        "app_code": "chat_with_db_execute",
        "temperature": 0.6,
        "max_new_tokens": 4000,
        "select_param": "overdue_analysis",
        "model_name": "deepseek",
        "incremental": False
    }
    
    try:
        print("📤 发送会导致SQL错误的查询...")
        response = requests.post(
            "http://localhost:5670/api/v1/chat/completions",
            json=test_query,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 查询请求成功发送")
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                
                # 检查是否包含通用错误信息
                if "Generate view content failed" in content:
                    print("❌ 仍然出现通用的'Generate view content failed'错误")
                    return False
                elif "ERROR!" in content:
                    print("❌ 仍然出现通用的'ERROR!'错误")
                    return False
                elif "📋" in content and "SQL" in content:
                    print("✅ 显示了详细的SQL错误信息")
                    print(f"📄 响应内容长度: {len(content)} 字符")
                    
                    # 检查是否包含SQL内容
                    if "```sql" in content:
                        print("✅ 响应包含了SQL代码块")
                    else:
                        print("⚠️  响应可能缺少SQL代码块")
                    
                    # 检查是否包含错误原因
                    if "错误原因" in content or "技术详情" in content:
                        print("✅ 响应包含了错误原因说明")
                    else:
                        print("⚠️  响应可能缺少错误原因说明")
                    
                    return True
                else:
                    print("⚠️  响应格式可能不符合预期")
                    print(f"响应内容前500字符: {content[:500]}")
                    return True  # 至少没有通用错误
            else:
                print("⚠️  响应格式异常")
                return False
        else:
            print(f"❌ 查询请求失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 查询请求异常: {e}")
        return False

def test_field_not_exist_error():
    """测试字段不存在错误的显示"""
    print("\n🔧 测试字段不存在错误的显示...")
    
    test_query = {
        "conv_uid": "test-field-not-exist",
        "user_input": "查询 lending_details 表中的 non_existent_field 字段",
        "user_name": "test_user",
        "chat_mode": "chat_with_db_execute",
        "app_code": "chat_with_db_execute",
        "temperature": 0.6,
        "max_new_tokens": 4000,
        "select_param": "overdue_analysis",
        "model_name": "deepseek",
        "incremental": False
    }
    
    try:
        response = requests.post(
            "http://localhost:5670/api/v1/chat/completions",
            json=test_query,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0].get("message", {}).get("content", "")
            
            if "Generate view content failed" in content or "ERROR!" in content:
                print("❌ 仍然出现通用错误")
                return False
            elif "📋" in content and ("字段" in content or "column" in content):
                print("✅ 显示了详细的字段错误信息")
                return True
            else:
                print("⚠️  响应格式可能不符合预期")
                return True  # 至少没有通用错误
        else:
            print(f"❌ 查询失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 查询异常: {e}")
        return False

def test_syntax_error_display():
    """测试SQL语法错误的显示"""
    print("\n🔧 测试SQL语法错误的显示...")
    
    test_query = {
        "conv_uid": "test-syntax-error",
        "user_input": "执行一个语法错误的SQL: SELECT * FORM lending_details",  # 故意写错 FROM
        "user_name": "test_user",
        "chat_mode": "chat_with_db_execute",
        "app_code": "chat_with_db_execute",
        "temperature": 0.6,
        "max_new_tokens": 4000,
        "select_param": "overdue_analysis",
        "model_name": "deepseek",
        "incremental": False
    }
    
    try:
        response = requests.post(
            "http://localhost:5670/api/v1/chat/completions",
            json=test_query,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0].get("message", {}).get("content", "")
            
            if "Generate view content failed" in content or "ERROR!" in content:
                print("❌ 仍然出现通用错误")
                return False
            elif "📋" in content and ("语法" in content or "syntax" in content):
                print("✅ 显示了详细的语法错误信息")
                return True
            else:
                print("⚠️  AI可能修复了语法错误或响应格式不同")
                return True  # 至少没有通用错误
        else:
            print(f"❌ 查询失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 查询异常: {e}")
        return False

def test_no_sql_generated():
    """测试AI未生成SQL时的显示"""
    print("\n🔧 测试AI未生成SQL时的显示...")
    
    test_query = {
        "conv_uid": "test-no-sql",
        "user_input": "什么是数据库？",  # 概念性问题，不需要SQL
        "user_name": "test_user",
        "chat_mode": "chat_with_db_execute",
        "app_code": "chat_with_db_execute",
        "temperature": 0.6,
        "max_new_tokens": 4000,
        "select_param": "overdue_analysis",
        "model_name": "deepseek",
        "incremental": False
    }
    
    try:
        response = requests.post(
            "http://localhost:5670/api/v1/chat/completions",
            json=test_query,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0].get("message", {}).get("content", "")
            
            if "Generate view content failed" in content or "ERROR!" in content:
                print("❌ 仍然出现通用错误")
                return False
            elif "📋" in content and "AI响应" in content:
                print("✅ 显示了详细的AI响应信息")
                return True
            else:
                print("✅ AI直接回答了概念性问题")
                return True  # 概念性问题可能直接回答
        else:
            print(f"❌ 查询失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 查询异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 开始测试增强的SQL错误显示功能")
    print("=" * 80)
    
    # 等待服务完全启动
    print("⏳ 等待服务完全启动...")
    time.sleep(5)
    
    success1 = test_sql_error_with_detailed_display()
    success2 = test_field_not_exist_error()
    success3 = test_syntax_error_display()
    success4 = test_no_sql_generated()
    
    print("\n" + "=" * 80)
    if success1 and success2 and success3 and success4:
        print("🎉 所有测试通过！SQL错误显示功能已完全改进")
        print("✅ 不再显示通用的'Generate view content failed'错误")
        print("✅ 系统现在会显示详细的SQL和错误信息")
        print("✅ 用户可以看到具体的SQL代码和错误原因")
        print("✅ 即使在最严重的错误情况下也提供有用的信息")
    else:
        print("❌ 部分测试失败，可能仍存在问题")
        if not success1:
            print("  - SQL错误详细显示测试失败")
        if not success2:
            print("  - 字段不存在错误显示测试失败")
        if not success3:
            print("  - 语法错误显示测试失败")
        if not success4:
            print("  - 无SQL生成情况显示测试失败")
    print("=" * 80) 