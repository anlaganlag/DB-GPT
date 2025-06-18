#!/bin/bash

# DB-GPT 数据源自动注册脚本
# 确保每次Docker重启都能正确加载数据库schema

echo "🚀 开始自动注册数据源..."

# 等待DB-GPT服务完全启动
echo "⏳ 等待DB-GPT服务启动..."
sleep 30

# 检查服务是否可用
while ! curl -s http://localhost:5670/api/health > /dev/null; do
    echo "⏳ 等待DB-GPT服务启动中..."
    sleep 10
done

echo "✅ DB-GPT服务已启动"

# 注册orange数据源
echo "📊 注册orange数据源..."

curl -X POST "http://localhost:5670/api/v1/datasources" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "orange",
    "type": "mysql",
    "host": "10.10.19.1",
    "port": 9030,
    "database": "orange",
    "username": "ai_user1",
    "password": "Weshare@2025",
    "description": "逾期率分析数据库(Apache Doris)",
    "sync_schema": true,
    "connect_args": {
      "charset": "utf8mb4",
      "autocommit": true
    }
  }'

echo ""
echo "⏳ 等待数据源同步..."
sleep 15

# 验证数据源是否注册成功
echo "🔍 验证数据源注册状态..."
response=$(curl -s "http://localhost:5670/api/v1/datasources")
if echo "$response" | grep -q "orange"; then
    echo "✅ 数据源注册成功！"
else
    echo "❌ 数据源注册失败，尝试备用方案..."
    
    # 备用方案：通过数据库直接插入
    echo "🔧 使用备用方案注册数据源..."
    docker-compose exec -T webserver python3 -c "
import sqlite3
import json
import os

# 连接到DB-GPT的元数据数据库
db_path = '/app/pilot/data/default_sqlite.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 插入数据源配置
    datasource_config = {
        'name': 'orange',
        'type': 'mysql',
        'host': '10.10.19.1',
        'port': 9030,
        'database': 'orange',
        'username': 'ai_user1',
        'password': 'Weshare@2025',
        'description': '逾期率分析数据库(Apache Doris)',
        'sync_schema': True
    }
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO datasource 
            (name, type, config, description, created_at, updated_at) 
            VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
        ''', (
            'orange', 
            'mysql', 
            json.dumps(datasource_config),
            '逾期率分析数据库(Apache Doris)'
        ))
        conn.commit()
        print('✅ 备用方案：数据源配置已写入数据库')
    except Exception as e:
        print(f'❌ 备用方案失败: {e}')
    finally:
        conn.close()
else:
    print('❌ 数据库文件不存在')
"
fi

# 重启webserver以加载新的数据源配置
echo "🔄 重启webserver以加载数据源配置..."
docker-compose restart webserver

echo "⏳ 等待服务重启..."
sleep 30

# 最终验证
echo "🎯 最终验证数据源状态..."
final_test=$(curl -X POST "http://localhost:5670/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chat_with_db_execute",
    "messages": [{"role": "user", "content": "显示数据库中的所有表"}],
    "chat_param": "orange",
    "temperature": 0.6
  }' 2>/dev/null)

if echo "$final_test" | grep -q "表结构信息不足"; then
    echo "❌ 数据源仍未正确加载"
    echo "💡 建议：请手动通过Web界面 http://localhost:5670 添加数据源"
else
    echo "✅ 数据源加载成功！"
fi

echo "🎉 数据源自动注册脚本执行完成" 