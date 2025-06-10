#!/usr/bin/env python3
"""
快速测试DB-GPT信息引导功能
"""

import requests
import json
import time

def test_guidance():
    """测试信息引导功能"""
    url = "http://localhost:5670/api/v1/chat/completions"
    
    # 测试查询：应该触发信息引导
    test_query = "帮我分析逾期率"
    
    payload = {
        "chat_mode": "chat_with_db_execute",
        "select_param": "test_db",
        "model_name": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "user_input": test_query,
        "conv_uid": f"test_{int(time.time())}",
        "chat_param": "test_db",
        "sys_code": None
    }
    
    print(f"🔍 测试查询: {test_query}")
    print("📡 发送请求...")
    
    try:
        response = requests.post(url, json=payload, timeout=30, stream=True)
        
        if response.status_code == 200:
            print("✅ 请求成功，解析响应...")
            
            content = ""
            for line in response.iter_lines():
                if line:
                    try:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str.strip() != '[DONE]':
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content += delta['content']
                    except json.JSONDecodeError:
                        continue
            
            print("\n" + "="*60)
            print("📋 AI响应内容:")
            print("="*60)
            print(content)
            print("="*60)
            
            # 分析响应质量
            guidance_indicators = [
                ("缺少", "识别缺失信息"),
                ("需要", "明确需求"),
                ("建议", "提供建议"),
                ("可以", "给出方案"),
                ("请", "主动引导"),
                ("您可以尝试", "具体指导"),
                ("如何定义", "深入了解"),
                ("哪个字段", "技术细节")
            ]
            
            print("\n📊 引导质量分析:")
            found_indicators = []
            for indicator, description in guidance_indicators:
                if indicator in content:
                    found_indicators.append(f"✅ {description}: 包含'{indicator}'")
                else:
                    found_indicators.append(f"❌ {description}: 未包含'{indicator}'")
            
            for indicator in found_indicators:
                print(f"   {indicator}")
            
            # 计算得分
            score = sum(1 for indicator, _ in guidance_indicators if indicator in content)
            total = len(guidance_indicators)
            percentage = (score / total) * 100
            
            print(f"\n🎯 引导质量得分: {score}/{total} ({percentage:.1f}%)")
            
            if percentage >= 75:
                print("🎉 优秀！信息引导功能工作良好")
            elif percentage >= 50:
                print("👍 良好！信息引导功能有明显改进")
            elif percentage >= 25:
                print("⚠️  一般！信息引导功能有所改善")
            else:
                print("🚨 需要改进！信息引导功能未达到预期")
            
            # 检查是否还是简单拒绝
            if "提供的表结构信息不足以生成 sql 查询" in content:
                print("❌ 警告：仍然使用旧的简单拒绝模式")
            else:
                print("✅ 已改进：不再使用简单拒绝模式")
                
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("🚀 快速测试DB-GPT信息引导功能...")
    test_guidance()
    print("\n🏁 测试完成！") 