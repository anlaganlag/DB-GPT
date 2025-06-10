#!/usr/bin/env python3
"""
测试增强的分析报告功能
验证当用户明确要求根因分析时，系统是否能生成详细的analysis_report
"""

import requests
import json
import time

def test_root_cause_analysis():
    """测试根因分析功能"""
    print("🔍 测试根因分析功能...")
    
    # 测试URL - 使用正确的v2端点
    url = "http://localhost:5670/api/v2/chat/completions"
    
    # 测试数据 - 明确要求根因分析
    test_data = {
        "model": "deepseek",
        "messages": [
            {
                "role": "user", 
                "content": "分析今年的逾期数据并找出根因。我们需要从lending_details表中提取5月份的逾期记录，并关联loan_info和customer_info表来分析可能的根因，如贷款金额、信用评分等。需要给出报告,给出详尽的根因分析报告"
            }
        ],
        "stream": False,
        "chat_mode": "chat_data",
        "chat_param": "overdue_analysis"
    }
    
    try:
        print("📤 发送请求...")
        response = requests.post(url, json=test_data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功")
            
            # 检查响应结构
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"📝 响应内容长度: {len(content)} 字符")
                
                # 检查是否包含分析报告关键词
                analysis_keywords = [
                    "分析报告", "analysis_report", "根因分析", "root cause",
                    "关键发现", "key_findings", "业务洞察", "insights",
                    "建议", "recommendations", "分析方法", "methodology"
                ]
                
                found_keywords = []
                for keyword in analysis_keywords:
                    if keyword in content:
                        found_keywords.append(keyword)
                
                print(f"🔍 找到的分析关键词: {found_keywords}")
                
                # 检查是否包含详细的分析内容
                has_detailed_analysis = any([
                    "📝 分析摘要" in content,
                    "🔍 关键发现" in content,
                    "💡 业务洞察" in content,
                    "📋 建议" in content,
                    "🔬 分析方法" in content
                ])
                
                if has_detailed_analysis:
                    print("✅ 响应包含详细的分析报告")
                    print("\n📋 响应内容预览:")
                    print("=" * 50)
                    print(content[:1000] + "..." if len(content) > 1000 else content)
                    print("=" * 50)
                    return True
                else:
                    print("❌ 响应缺少详细的分析报告")
                    print(f"📄 完整响应: {content}")
                    return False
            else:
                print("❌ 响应格式异常")
                print(f"📄 完整响应: {result}")
                return False
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"📄 错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

def test_simple_query():
    """测试普通查询（不要求分析报告）"""
    print("\n🔍 测试普通查询功能...")
    
    url = "http://localhost:5670/api/v2/chat/completions"
    
    test_data = {
        "model": "deepseek",
        "messages": [
            {
                "role": "user", 
                "content": "查询5月份的贷款记录，显示前10条"
            }
        ],
        "stream": False,
        "chat_mode": "chat_data",
        "chat_param": "overdue_analysis"
    }
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 普通查询不应该包含详细分析报告
            has_analysis_report = any([
                "📝 分析摘要" in content,
                "🔍 关键发现" in content,
                "💡 业务洞察" in content
            ])
            
            if not has_analysis_report:
                print("✅ 普通查询正确，没有生成不必要的分析报告")
                return True
            else:
                print("⚠️ 普通查询意外生成了分析报告")
                return False
        else:
            print(f"❌ 普通查询失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 普通查询测试错误: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试增强的分析报告功能")
    print("=" * 60)
    
    # 等待服务完全启动
    print("⏳ 等待服务启动...")
    time.sleep(5)
    
    # 测试结果
    test_results = []
    
    # 测试1: 根因分析
    result1 = test_root_cause_analysis()
    test_results.append(("根因分析测试", result1))
    
    # 测试2: 普通查询
    result2 = test_simple_query()
    test_results.append(("普通查询测试", result2))
    
    # 总结测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！增强的分析报告功能工作正常。")
    else:
        print("⚠️ 部分测试失败，需要进一步检查。")
    
    return all_passed

if __name__ == "__main__":
    main() 