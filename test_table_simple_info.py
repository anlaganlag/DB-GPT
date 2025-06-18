#!/usr/bin/env python3

import pymysql
import sys
import os

def test_table_simple_info_direct():
    """直接测试数据库连接和表结构查询"""
    
    print("🔍 直接测试数据库连接和表结构查询...")
    
    try:
        # 直接连接数据库
        print("📡 建立数据库连接...")
        conn = pymysql.connect(
            host='10.10.19.1',
            port=9030,
            user='ai_user1',
            password='Weshare@2025',
            database='orange',
            charset='utf8mb4',
            autocommit=True
        )
        
        cursor = conn.cursor()
        
        # 测试基本连接
        print("\n🧪 测试基本连接...")
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print(f"✅ 基本连接测试: {result}")
        
        # 测试数据库名查询
        print("\n🔍 测试数据库名查询...")
        try:
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            print(f"✅ 当前数据库: {db_name}")
        except Exception as e:
            print(f"❌ DATABASE()查询失败: {e}")
            # 尝试其他方式
            try:
                cursor.execute("SELECT SCHEMA()")
                db_name = cursor.fetchone()[0]
                print(f"✅ SCHEMA()查询: {db_name}")
            except Exception as e2:
                print(f"❌ SCHEMA()查询也失败: {e2}")
                db_name = "orange"  # 使用默认值
                
        # 测试表查询
        print("\n📋 测试SHOW TABLES...")
        try:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"✅ SHOW TABLES返回: {len(tables)}个表")
            if tables:
                table_names = [t[0] for t in tables]
                print(f"  前10个表: {table_names[:10]}")
            else:
                print("❌ SHOW TABLES返回空结果")
        except Exception as e:
            print(f"❌ SHOW TABLES失败: {e}")
            
        # 测试information_schema查询
        print("\n🔍 测试information_schema查询...")
        try:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                (db_name,)
            )
            tables = cursor.fetchall()
            print(f"✅ information_schema查询返回: {len(tables)}个表")
            if tables:
                table_names = [t[0] for t in tables]
                print(f"  前10个表: {table_names[:10]}")
        except Exception as e:
            print(f"❌ information_schema查询失败: {e}")
            
        # 模拟table_simple_info的SQL查询
        print("\n🎯 测试table_simple_info SQL...")
        try:
            # 这是DB-GPT中MySQL连接器使用的SQL
            sql = f"""
                select concat(table_name, "(" , group_concat(column_name), ")")
                as schema_info from information_schema.COLUMNS where
                table_schema="{db_name}" group by TABLE_NAME;
            """
            print(f"执行SQL: {sql}")
            
            cursor.execute(sql)
            results = cursor.fetchall()
            print(f"✅ table_simple_info SQL返回: {len(results)}条结果")
            
            if results:
                print("✅ 前5个表结构信息:")
                for i, result in enumerate(results[:5]):
                    print(f"  {i+1}. {result[0]}")
            else:
                print("❌ table_simple_info SQL返回空结果!")
                
                # 尝试调试
                print("\n🔍 调试为什么返回空结果...")
                
                # 检查table_schema值
                cursor.execute("SELECT DISTINCT table_schema FROM information_schema.COLUMNS LIMIT 10")
                schemas = cursor.fetchall()
                print(f"可用的table_schema: {[s[0] for s in schemas]}")
                
                # 检查是否有orange数据库的列信息
                cursor.execute("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE table_schema = %s", (db_name,))
                count = cursor.fetchone()[0]
                print(f"orange数据库的列数量: {count}")
                
                if count == 0:
                    # 尝试不指定schema
                    print("尝试不指定schema查询...")
                    cursor.execute("""
                        select concat(table_name, "(" , group_concat(column_name), ")")
                        as schema_info from information_schema.COLUMNS 
                        group by TABLE_NAME LIMIT 5;
                    """)
                    results = cursor.fetchall()
                    print(f"不指定schema的结果: {len(results)}条")
                    for result in results:
                        print(f"  {result[0]}")
                        
        except Exception as e:
            print(f"❌ table_simple_info SQL失败: {e}")
            import traceback
            traceback.print_exc()
            
        conn.close()
        print("\n✅ 测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_table_simple_info_direct() 