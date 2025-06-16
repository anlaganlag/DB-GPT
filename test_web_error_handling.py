#!/usr/bin/env python3
"""
Test Web Interface SQL Error Handling
测试Web界面SQL错误处理功能

This script tests the enhanced SQL error handling through the web interface
to ensure users see detailed error information instead of generic messages.
"""

import requests
import json
import time

def test_database_connection():
    """Test if DB-GPT is running and accessible"""
    try:
        response = requests.get("http://localhost:5670", timeout=5)
        if response.status_code == 200:
            print("✅ DB-GPT服务正在运行")
            return True
        else:
            print(f"⚠️ DB-GPT服务状态异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ 无法连接到DB-GPT服务 (http://localhost:5670)")
        print("请确保DB-GPT容器正在运行")
        return False

def test_sql_error_scenarios():
    """Test various SQL error scenarios through the web interface"""
    
    base_url = "http://localhost:5670"
    
    # Test cases with different types of SQL errors
    test_cases = [
        {
            "name": "表不存在错误",
            "query": "查询表xyz_nonexistent_table中的所有数据",
            "expected_improvements": [
                "应该显示具体的SQL查询",
                "应该说明表不存在",
                "不应该显示通用错误消息"
            ]
        },
        {
            "name": "字段不存在错误", 
            "query": "从customer_info表中查询字段xyz_nonexistent_column",
            "expected_improvements": [
                "应该显示执行的SQL",
                "应该说明字段不存在",
                "应该提供修复建议"
            ]
        },
        {
            "name": "正常查询测试",
            "query": "查询customer_info表中的前5条记录",
            "expected_improvements": [
                "应该正常返回数据",
                "应该显示表格格式"
            ]
        }
    ]
    
    print("🧪 开始测试Web界面SQL错误处理功能...")
    print("="*80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print(f"🔍 查询: {test_case['query']}")
        print("-" * 60)
        
        try:
            # Test the chat API endpoint
            chat_response = test_chat_api(base_url, test_case['query'])
            
            if chat_response:
                analyze_response(chat_response, test_case)
            else:
                print("❌ 无法获取有效响应")
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
        
        print("\n" + "="*80)
        time.sleep(2)

def test_chat_api(base_url, query):
    """Test the chat API with a specific query"""
    
    try:
        # Try the chat completions API
        response = requests.post(
            f"{base_url}/api/v1/chat/completions",
            json={
                "model": "chatdb_qa",
                "messages": [{"role": "user", "content": query}],
                "stream": False
            },
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            return content
        else:
            print(f"❌ API错误: {response.status_code}")
            print(f"响应: {response.text[:200]}...")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {str(e)}")
        return None

def analyze_response(content, test_case):
    """Analyze the response to check for error handling improvements"""
    
    print(f"📄 响应内容 (前500字符):")
    print(content[:500] + "..." if len(content) > 500 else content)
    print()
    
    # Check for error handling improvements
    improvements_found = []
    issues_found = []
    
    # Positive checks (what we want to see)
    if "📝" in content and ("SQL" in content or "sql" in content):
        improvements_found.append("✅ 显示了SQL查询内容")
    
    if any(indicator in content for indicator in ["🔍", "❌", "错误原因", "失败"]):
        improvements_found.append("✅ 提供了具体错误信息")
    
    if any(indicator in content for indicator in ["💡", "建议", "尝试", "检查"]):
        improvements_found.append("✅ 给出了修复建议")
    
    if "技术详情" in content or "详细信息" in content:
        improvements_found.append("✅ 提供了技术详情")
    
    # Negative checks (what we don't want to see)
    if "Generate view content failed" in content:
        issues_found.append("❌ 仍然显示通用错误消息")
    
    if "AppActionException" in content:
        issues_found.append("❌ 显示了技术异常信息")
    
    # Check for successful data display (for normal queries)
    if "|" in content and "---" in content:
        improvements_found.append("✅ 正确显示了表格数据")
    
    # Report findings
    if improvements_found:
        print("🎉 错误处理改进验证:")
        for improvement in improvements_found:
            print(f"   {improvement}")
    
    if issues_found:
        print("⚠️ 发现的问题:")
        for issue in issues_found:
            print(f"   {issue}")
    
    if not improvements_found and not issues_found:
        print("🤔 无法确定错误处理状态，需要人工检查")

def main():
    """Main test function"""
    print("🚀 DB-GPT Web界面SQL错误处理测试")
    print("="*80)
    
    # First check if DB-GPT is running
    if test_database_connection():
        print("\n开始错误处理功能测试...\n")
        test_sql_error_scenarios()
        
        print("\n🎯 测试总结:")
        print("✅ 如果看到详细的SQL错误信息而不是'Generate view content failed'，")
        print("   说明错误处理改进功能正常工作")
        print("✅ 系统应该显示具体的SQL查询、错误原因和修复建议")
        
    else:
        print("\n❌ 测试终止: DB-GPT服务不可用")
        print("\n🔧 启动DB-GPT的命令:")
        print("   sudo docker start dbgpt-webserver")
        print("   或")
        print("   cd /home/weshare/DB-GPT && sudo docker compose up -d")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
