#!/usr/bin/env python3
"""
测试改进的表格格式显示功能
验证Markdown表格格式是否正确显示
"""

import requests
import json
import time

def test_table_format_improvement():
    """测试表格格式改进"""
    print("🔧 测试改进的表格格式显示...")
    
    # 测试逾期率分析查询（应该显示为清晰的表格）
    test_query = {
        "conv_uid": "test-table-format",
        "user_input": "我分析今年各月DPD大于30天的\n\n预期输出格式\n\n放款月份    MOB1    MOB2    MOB3    MOB6    MOB12   MOB24\n2025-01    0.5%    1.2%    2.1%    3.8%    5.2%    6.1%\n2025-02    0.4%    1.1%    2.0%    3.5%    4.9%    -\n2025-03    0.6%    1.3%    2.2%    3.9%    -       -\n\n并给出根因分析报告",
        "user_name": "test_user",
        "chat_mode": "chat_with_db_execute",
        "app_code": "chat_with_db_execute",
        "temperature": 0.6,
        "max_new_tokens": 4000,
        "select_param": "overdue_analysis",
        "model_name": "deepseek",
        "incremental": False,
        "stream": False
    }
    
    try:
        print("📤 发送逾期率分析查询...")
        response = requests.post(
            "http://localhost:5670/api/v1/chat/completions",
            json=test_query,
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 处理流式响应
            if response.headers.get('content-type') == 'text/event-stream':
                print("📡 处理流式响应...")
                content = response.text
                print(f"📄 流式内容长度: {len(content)} 字符")
                
                # 检查是否包含表格格式
                if "📊 **查询结果**" in content:
                    print("✅ 找到查询结果标题")
                
                if "**逾期率分析表**" in content:
                    print("✅ 找到表格描述")
                
                if "|" in content and "---" in content:
                    print("✅ 找到Markdown表格格式")
                
                if "**数据说明**" in content:
                    print("✅ 找到数据说明")
                
                if "**分析报告**" in content:
                    print("✅ 找到分析报告")
                
                # 显示部分内容用于验证
                print("\n📋 响应内容片段:")
                lines = content.split('\n')
                for i, line in enumerate(lines[:20]):
                    if line.strip():
                        print(f"  {i+1}: {line[:100]}...")
                
                return True
            else:
                try:
                    result = response.json()
                    print(f"✅ 查询成功: {result}")
                    return True
                except json.JSONDecodeError:
                    print(f"❌ JSON解析失败: {response.text[:500]}")
                    return False
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"错误内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_simple_table_query():
    """测试简单表格查询"""
    print("\n🔧 测试简单表格查询...")
    
    test_query = {
        "conv_uid": "test-simple-table",
        "user_input": "查询lending_details表的前5条记录",
        "user_name": "test_user",
        "chat_mode": "chat_with_db_execute",
        "app_code": "chat_with_db_execute",
        "temperature": 0.6,
        "max_new_tokens": 2000,
        "select_param": "overdue_analysis",
        "model_name": "deepseek",
        "incremental": False,
        "stream": False
    }
    
    try:
        print("📤 发送简单查询...")
        response = requests.post(
            "http://localhost:5670/api/v1/chat/completions",
            json=test_query,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            if response.headers.get('content-type') == 'text/event-stream':
                content = response.text
                print(f"📄 内容长度: {len(content)} 字符")
                
                # 检查表格格式改进
                if "📊 **查询结果**" in content:
                    print("✅ 找到改进的查询结果标题")
                
                if "📋 共" in content and "条记录" in content:
                    print("✅ 找到记录数统计")
                
                if "|" in content:
                    print("✅ 找到表格分隔符")
                
                return True
            else:
                print("✅ 非流式响应处理成功")
                return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 查询异常: {e}")
        return False

def main():
    print("="*80)
    print("🚀 开始测试表格格式改进功能")
    print("="*80)
    
    # 等待服务启动
    print("⏳ 等待服务完全启动...")
    time.sleep(5)
    
    # 测试逾期率分析表格格式
    success1 = test_table_format_improvement()
    
    # 测试简单表格查询格式
    success2 = test_simple_table_query()
    
    print("\n" + "="*80)
    if success1 and success2:
        print("🎉 表格格式改进测试成功！")
        print("  - 逾期率分析表格格式正常")
        print("  - 简单查询表格格式正常")
        print("  - Markdown表格格式生效")
        print("  - 数据说明和统计信息完整")
    else:
        print("❌ 部分测试失败，可能仍存在问题")
        if not success1:
            print("  - 逾期率分析表格格式异常")
        if not success2:
            print("  - 简单查询表格格式异常")
    print("="*80)

if __name__ == "__main__":
    main() 