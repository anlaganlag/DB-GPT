#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试AI响应格式的脚本
直接测试AI模型是否按照期望的JSON格式返回响应
"""

import requests
import json
import time

def test_ai_response():
    """测试AI模型的响应格式"""
    
    # DB-GPT API端点
    api_url = "http://localhost:5670/api/v1/chat/completions"
    
    # 测试prompt - 简化版本
    test_prompt = """
你是一个数据库查询助手。请根据用户的问题生成SQL查询。

数据库表结构：
- overdue_rate_stats: 逾期率统计表
  - stat_date: 统计日期
  - loan_month: 贷款月份
  - mob: MOB期数
  - total_loans: 总贷款数
  - total_amount: 总金额
  - overdue_loans: 逾期贷款数
  - overdue_amount: 逾期金额
  - overdue_rate: 逾期率
  - dpd_threshold: DPD阈值

用户问题：显示逾期率数据

请严格按照以下JSON格式返回：
{
    "thoughts": "分析用户需求的思考过程",
    "sql": "生成的SQL查询语句",
    "display_type": "response_table",
    "direct_response": "对用户的直接回复"
}
"""

    payload = {
        "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": test_prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
        "stream": False
    }
    
    try:
        print("🚀 发送测试请求到AI模型...")
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            print("✅ AI响应成功")
            print(f"📝 原始响应:\n{ai_response}")
            print("\n" + "="*50)
            
            # 尝试解析JSON
            try:
                parsed_json = json.loads(ai_response)
                print("✅ JSON解析成功")
                print(f"📊 解析结果: {json.dumps(parsed_json, indent=2, ensure_ascii=False)}")
                
                # 检查必需字段
                required_fields = ['thoughts', 'sql', 'display_type', 'direct_response']
                missing_fields = [field for field in required_fields if field not in parsed_json]
                
                if missing_fields:
                    print(f"⚠️  缺少字段: {missing_fields}")
                else:
                    print("✅ 所有必需字段都存在")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败: {e}")
                print("🔍 这可能是导致'Generate view content failed'错误的原因")
                
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def test_with_db_chat_prompt():
    """使用实际的DB-Chat prompt测试"""
    
    # 从实际的prompt文件中获取prompt
    try:
        with open('packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/prompt.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("📋 使用实际的DB-Chat prompt进行测试...")
        print("请在DB-GPT界面中发送查询，然后查看日志输出")
        
    except Exception as e:
        print(f"❌ 无法读取prompt文件: {e}")

if __name__ == "__main__":
    print("🔧 AI响应格式调试工具")
    print("="*50)
    
    # 首先测试简化版本
    test_ai_response()
    
    print("\n" + "="*50)
    test_with_db_chat_prompt() 