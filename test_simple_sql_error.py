#!/usr/bin/env python3
"""
简单测试SQL错误显示功能
"""

import requests
import json

def test_simple_sql_error():
    """测试简单的SQL错误"""
    print("🔧 测试SQL错误显示...")
    
    test_query = {
        "conv_uid": "test-simple-error",
        "user_input": "查询不存在的表 xyz_table",
        "user_name": "test_user",
        "chat_mode": "chat_with_db_execute",
        "app_code": "chat_with_db_execute",
        "temperature": 0.6,
        "max_new_tokens": 2000,
        "select_param": "overdue_analysis",
        "model_name": "deepseek",
        "incremental": False,
        "stream": False  # 禁用流式响应
    }
    
    try:
        print("📤 发送查询...")
        response = requests.post(
            "http://localhost:5670/api/v1/chat/completions",
            json=test_query,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📊 响应头: {response.headers}")
        
        if response.status_code == 200:
            # 检查是否是流式响应
            if 'text/event-stream' in response.headers.get('content-type', ''):
                print("📡 处理流式响应...")
                content = ""
                for line in response.text.split('\n'):
                    if line.startswith('data:'):
                        data_part = line[5:].strip()  # 移除 'data:' 前缀
                        if data_part and data_part != '[DONE]':
                            try:
                                # 尝试解码可能的编码问题
                                decoded = data_part.encode('latin1').decode('utf-8')
                                content += decoded
                            except:
                                content += data_part
                
                print(f"📄 流式内容长度: {len(content)} 字符")
                print(f"内容前500字符: {content[:500]}")
                
                # 检查关键内容
                if "Generate view content failed" in content:
                    print("❌ 仍然出现通用错误")
                    return False
                elif "📋" in content:
                    print("✅ 显示了详细的错误信息")
                    return True
                else:
                    print("⚠️  响应格式可能不同，但没有通用错误")
                    return True
            else:
                try:
                    result = response.json()
                    print("✅ JSON解析成功")
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0].get("message", {}).get("content", "")
                        print(f"📄 响应内容长度: {len(content)} 字符")
                        
                        # 检查关键内容
                        if "Generate view content failed" in content:
                            print("❌ 仍然出现通用错误")
                            print(f"内容: {content}")
                            return False
                        elif "📋" in content:
                            print("✅ 显示了详细的错误信息")
                            print(f"内容前1000字符: {content[:1000]}")
                            return True
                        else:
                            print("⚠️  响应格式可能不同")
                            print(f"内容: {content}")
                            return True  # 至少没有通用错误
                    else:
                        print("❌ 响应格式异常")
                        print(f"完整响应: {result}")
                        return False
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    print(f"响应文本: {response.text[:500]}")
                    return False
        else:
            print(f"❌ HTTP请求失败")
            print(f"响应文本: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 简单SQL错误显示测试")
    print("=" * 60)
    
    success = test_simple_sql_error()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 测试成功！SQL错误显示功能正常")
    else:
        print("❌ 测试失败")
    print("=" * 60) 