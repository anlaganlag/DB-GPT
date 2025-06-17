#!/bin/bash

# DB-GPT 数据源自动初始化脚本
# 确保orange数据源配置正确

echo "🔧 开始检查和修复数据源配置..."

# 检查webserver容器是否运行
if ! docker ps | grep -q "db-gpt_webserver_1"; then
    echo "❌ webserver容器未运行，请先启动项目"
    exit 1
fi

# 等待容器完全启动
echo "⏳ 等待webserver完全启动..."
sleep 10

# 检查当前数据源配置
echo "📋 检查当前数据源配置..."
CURRENT_CONFIG=$(docker exec -i db-gpt_webserver_1 sqlite3 /app/pilot/data/dbgpt.db "SELECT db_name, db_type, db_host, db_port, db_path FROM connect_config WHERE db_name='orange';" 2>/dev/null)

if [ -z "$CURRENT_CONFIG" ]; then
    echo "❌ 未找到orange数据源配置，正在创建..."
    
    # 创建数据源配置
    docker exec -i db-gpt_webserver_1 sqlite3 /app/pilot/data/dbgpt.db "
    INSERT INTO connect_config (db_name, db_type, db_host, db_port, db_user, db_pwd, db_path, comment) 
    VALUES ('orange', 'mysql', '10.10.19.1', 9030, 'ai_user1', 'Weshare@2025', 'orange', '逾期率分析数据库(Apache Doris伪装成MySQL)');
    "
    echo "✅ 数据源配置已创建"
else
    echo "📊 当前配置: $CURRENT_CONFIG"
    
    # 检查db_path是否为空
    DB_PATH=$(echo "$CURRENT_CONFIG" | cut -d'|' -f5)
    if [ -z "$DB_PATH" ]; then
        echo "🔧 修复db_path字段..."
        docker exec -i db-gpt_webserver_1 sqlite3 /app/pilot/data/dbgpt.db "
        UPDATE connect_config SET db_path='orange' WHERE db_name='orange';
        "
        echo "✅ db_path字段已修复"
    fi
    
    # 检查db_type是否为mysql
    DB_TYPE=$(echo "$CURRENT_CONFIG" | cut -d'|' -f2)
    if [ "$DB_TYPE" != "mysql" ]; then
        echo "🔧 修复db_type字段..."
        docker exec -i db-gpt_webserver_1 sqlite3 /app/pilot/data/dbgpt.db "
        UPDATE connect_config SET db_type='mysql' WHERE db_name='orange';
        "
        echo "✅ db_type字段已修复"
    fi
fi

# 验证连接
echo "🔍 验证数据库连接..."
CONNECTION_TEST=$(docker exec -i db-gpt_webserver_1 python3 -c "
import pymysql
try:
    conn = pymysql.connect(
        host='10.10.19.1',
        port=9030,
        user='ai_user1',
        password='Weshare@2025',
        database='orange',
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    cursor.execute('SHOW TABLES;')
    tables = cursor.fetchall()
    print(f'SUCCESS:{len(tables)}')
    conn.close()
except Exception as e:
    print(f'ERROR:{e}')
" 2>/dev/null)

if [[ $CONNECTION_TEST == SUCCESS:* ]]; then
    TABLE_COUNT=$(echo "$CONNECTION_TEST" | cut -d':' -f2)
    echo "✅ 数据库连接正常，找到 $TABLE_COUNT 个表"
else
    echo "❌ 数据库连接失败: $CONNECTION_TEST"
    exit 1
fi

# 显示最终配置
echo ""
echo "📋 最终数据源配置:"
docker exec -i db-gpt_webserver_1 sqlite3 /app/pilot/data/dbgpt.db "
SELECT 
    'Name: ' || db_name || char(10) ||
    'Type: ' || db_type || char(10) ||
    'Host: ' || db_host || ':' || db_port || char(10) ||
    'Database: ' || db_path || char(10) ||
    'User: ' || db_user || char(10) ||
    'Comment: ' || COALESCE(comment, 'None')
FROM connect_config WHERE db_name='orange';
"

echo ""
echo "🎉 数据源配置检查完成！"
echo "💡 现在可以在Web界面中正常使用orange数据源了"
echo "🌐 Web界面地址: http://localhost:5670" 