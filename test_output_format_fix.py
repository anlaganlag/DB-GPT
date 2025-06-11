#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试输出格式修复效果
Test output format fix effectiveness
"""

import requests
import json
import time

def test_format_requirement():
    """测试用户指定输出格式的处理"""
    print("🧪 测试用户指定输出格式处理")
    print("=" * 60)
    
    # 模拟用户的完整请求
    user_query = """帮我分析今年各月DPD大于30天的

预期输出格式

放款月份    MOB1    MOB2    MOB3    MOB6    MOB12   MOB24
2025-01    0.5%    1.2%    2.1%    3.8%    5.2%    6.1%
2025-02    0.4%    1.1%    2.0%    3.5%    4.9%    -
2025-03    0.6%    1.3%    2.2%    3.9%    -       -

并给出根因分析报告"""
    
    print(f"📝 用户查询: {user_query}")
    print("\n🔍 期望结果:")
    print("- SQL应该生成PIVOT格式查询（宽格式）")
    print("- 列应该包含: 放款月份, MOB1, MOB2, MOB3, MOB6, MOB12, MOB24")
    print("- 每行显示一个月份的所有MOB数据")
    print("- 不应该是长格式（每行一个月份+MOB组合）")
    
    # 构造API请求
    api_url = "http://localhost:5670/api/v1/chat/completions"
    
    payload = {
        "model": "deepseek",
        "messages": [
            {
                "role": "user", 
                "content": user_query
            }
        ],
        "stream": False,
        "chat_mode": "chat_with_db_execute",
        "chat_param": "overdue_analysis"
    }
    
    try:
        print("\n🚀 发送API请求...")
        response = requests.post(api_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API请求成功")
            
            # 解析响应
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(f"\n📋 AI响应内容:")
                print("-" * 40)
                print(content)
                print("-" * 40)
                
                # 分析响应格式
                print("\n🔍 格式分析:")
                if "MOB1" in content and "MOB2" in content and "MOB3" in content:
                    print("✅ 检测到PIVOT格式列名 (MOB1, MOB2, MOB3...)")
                else:
                    print("❌ 未检测到PIVOT格式列名")
                
                if "放款月份" in content or "loan_month" in content:
                    print("✅ 检测到月份分组字段")
                else:
                    print("❌ 未检测到月份分组字段")
                
                # 检查是否是长格式
                lines = content.split('\n')
                data_lines = [line for line in lines if '2025-' in line and ('0.' in line or '%' in line)]
                
                if len(data_lines) > 0:
                    print(f"📊 数据行数: {len(data_lines)}")
                    
                    # 分析第一行数据格式
                    first_data_line = data_lines[0]
                    print(f"📝 第一行数据: {first_data_line}")
                    
                    # 计算列数（简单估算）
                    columns = len([x for x in first_data_line.split() if x.strip()])
                    print(f"📊 估算列数: {columns}")
                    
                    if columns >= 6:  # 月份 + 6个MOB列
                        print("✅ 可能是宽格式（PIVOT）- 一行包含多个MOB数据")
                    else:
                        print("❌ 可能是长格式 - 每行只有少量列")
                
                # 检查分析报告
                if "analysis_report" in content or "分析报告" in content or "根因分析" in content:
                    print("✅ 包含分析报告")
                else:
                    print("❌ 缺少分析报告")
                    
            else:
                print("❌ 响应格式异常")
                
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def main():
    """主函数"""
    print("🔧 输出格式修复效果测试")
    print("=" * 60)
    print("测试目标: 验证AI是否按照用户指定的输出格式生成SQL")
    print("修复内容: 在prompt中添加了用户指定格式处理规则")
    print()
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(10)
    
    # 测试格式要求处理
    test_format_requirement()
    
    print("\n" + "=" * 60)
    print("🎯 测试完成!")
    print("如果AI仍然生成长格式，可能需要:")
    print("1. 检查prompt是否正确更新到容器中")
    print("2. 清理浏览器缓存重新测试")
    print("3. 考虑在SQL后处理中添加格式转换逻辑")

if __name__ == "__main__":
    main() 