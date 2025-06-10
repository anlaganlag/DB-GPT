#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逾期率数据展示测试脚本
验证生成的数据能够正确展示在报表中
"""

import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'password': 'aa123456',
    'database': 'overdue_analysis'
}

def connect_database():
    """连接数据库"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ 数据库连接成功")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def test_user_query(conn):
    """测试用户原始查询"""
    print("\n" + "="*50)
    print("📊 测试用户原始查询")
    print("="*50)
    
    query = """
    SELECT
      stat_date AS '统计日期',
      loan_month AS '贷款月份',
      mob AS 'Month of Book',
      total_loans AS '总贷款数',
      total_amount AS '总金额',
      overdue_loans AS '逾期贷款数',
      overdue_amount AS '逾期金额',
      overdue_rate AS '逾期率',
      dpd_threshold AS 'DPD阈值'
    FROM
      overdue_rate_stats
    WHERE
      loan_month = '2023-05'
      AND stat_date = '2023-05-31'
    ORDER BY
      dpd_threshold ASC
    LIMIT
      50;
    """
    
    try:
        df = pd.read_sql(query, conn)
        print(f"✅ 查询成功，返回 {len(df)} 条记录")
        print("\n📋 查询结果预览:")
        print(df.head(10).to_string(index=False))
        return df
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return None

def test_trend_analysis(conn):
    """测试趋势分析"""
    print("\n" + "="*50)
    print("📈 测试逾期率趋势分析")
    print("="*50)
    
    query = """
    SELECT 
        loan_month as '贷款月份',
        mob as 'MOB期数',
        overdue_rate as '逾期率',
        dpd_threshold as 'DPD阈值'
    FROM overdue_rate_stats
    WHERE dpd_threshold = 30
    ORDER BY loan_month, mob;
    """
    
    try:
        df = pd.read_sql(query, conn)
        print(f"✅ 趋势查询成功，返回 {len(df)} 条记录")
        print("\n📋 30天逾期率趋势:")
        print(df.to_string(index=False))
        return df
    except Exception as e:
        print(f"❌ 趋势查询失败: {e}")
        return None

def test_data_completeness(conn):
    """测试数据完整性"""
    print("\n" + "="*50)
    print("🔍 测试数据完整性")
    print("="*50)
    
    queries = {
        "总记录数": "SELECT COUNT(*) as count FROM overdue_rate_stats",
        "月份数": "SELECT COUNT(DISTINCT loan_month) as count FROM overdue_rate_stats",
        "DPD阈值数": "SELECT COUNT(DISTINCT dpd_threshold) as count FROM overdue_rate_stats",
        "MOB期数": "SELECT COUNT(DISTINCT mob) as count FROM overdue_rate_stats",
        "日期范围": "SELECT MIN(stat_date) as min_date, MAX(stat_date) as max_date FROM overdue_rate_stats"
    }
    
    for name, query in queries.items():
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            if name == "日期范围":
                print(f"✅ {name}: {result[0]} 到 {result[1]}")
            else:
                print(f"✅ {name}: {result[0]}")
            cursor.close()
        except Exception as e:
            print(f"❌ {name} 查询失败: {e}")

def test_business_logic(conn):
    """测试业务逻辑合理性"""
    print("\n" + "="*50)
    print("🧮 测试业务逻辑合理性")
    print("="*50)
    
    # 检查逾期率是否随DPD阈值递减
    query = """
    SELECT 
        dpd_threshold,
        AVG(overdue_rate) as avg_rate
    FROM overdue_rate_stats
    GROUP BY dpd_threshold
    ORDER BY dpd_threshold;
    """
    
    try:
        df = pd.read_sql(query, conn)
        print("📊 各DPD阈值的平均逾期率:")
        print(df.to_string(index=False))
        
        # 验证逾期率递减逻辑
        rates = df['avg_rate'].tolist()
        is_decreasing = all(rates[i] >= rates[i+1] for i in range(len(rates)-1))
        
        if is_decreasing:
            print("✅ 逾期率随DPD阈值递减，符合业务逻辑")
        else:
            print("⚠️  逾期率未完全递减，需要检查数据")
            
    except Exception as e:
        print(f"❌ 业务逻辑检查失败: {e}")

def test_report_scenarios(conn):
    """测试常见报表场景"""
    print("\n" + "="*50)
    print("📊 测试常见报表场景")
    print("="*50)
    
    scenarios = {
        "月度逾期率对比": """
            SELECT 
                loan_month as '月份',
                ROUND(AVG(CASE WHEN dpd_threshold = 30 THEN overdue_rate END), 2) as 'M1+逾期率',
                ROUND(AVG(CASE WHEN dpd_threshold = 60 THEN overdue_rate END), 2) as 'M2+逾期率',
                ROUND(AVG(CASE WHEN dpd_threshold = 90 THEN overdue_rate END), 2) as 'M3+逾期率'
            FROM overdue_rate_stats
            GROUP BY loan_month
            ORDER BY loan_month;
        """,
        
        "MOB期数逾期率分析": """
            SELECT 
                mob as 'MOB期数',
                ROUND(AVG(CASE WHEN dpd_threshold = 30 THEN overdue_rate END), 2) as '平均M1+逾期率'
            FROM overdue_rate_stats
            WHERE loan_month = '2023-05'
            GROUP BY mob
            ORDER BY mob;
        """,
        
        "逾期金额统计": """
            SELECT 
                loan_month as '月份',
                SUM(total_amount) as '总放款金额',
                SUM(CASE WHEN dpd_threshold = 30 THEN overdue_amount END) as 'M1+逾期金额',
                ROUND(SUM(CASE WHEN dpd_threshold = 30 THEN overdue_amount END) / SUM(total_amount) * 100, 2) as '逾期金额占比%'
            FROM overdue_rate_stats
            GROUP BY loan_month
            ORDER BY loan_month;
        """
    }
    
    for scenario_name, query in scenarios.items():
        print(f"\n📈 {scenario_name}:")
        try:
            df = pd.read_sql(query, conn)
            print(df.to_string(index=False))
            print("✅ 查询成功")
        except Exception as e:
            print(f"❌ 查询失败: {e}")

def main():
    """主函数"""
    print("🚀 开始逾期率数据展示测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 连接数据库
    conn = connect_database()
    if not conn:
        return
    
    try:
        # 执行各项测试
        test_user_query(conn)
        test_trend_analysis(conn)
        test_data_completeness(conn)
        test_business_logic(conn)
        test_report_scenarios(conn)
        
        print("\n" + "="*50)
        print("🎉 所有测试完成！")
        print("✅ 数据已成功生成，可以在DB-GPT中进行逾期率分析")
        print("💡 建议在DB-GPT中尝试以下查询:")
        print("   - '帮我分析逾期率趋势'")
        print("   - '显示2023年5月的逾期率数据'")
        print("   - '对比不同MOB期数的逾期表现'")
        print("   - '分析M1、M2、M3逾期率的变化'")
        print("="*50)
        
    finally:
        conn.close()
        print("🔌 数据库连接已关闭")

if __name__ == "__main__":
    main() 