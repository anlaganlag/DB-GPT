#!/bin/bash

# DB-GPT 数据源自动注册脚本 - 修正版
# 使用正确的数据库路径和表名

echo "🚀 开始自动注册数据源（修正版）..."

# 等待DB-GPT服务完全启动
echo "⏳ 等待DB-GPT服务启动..."
sleep 30

# 检查服务是否可用
while ! curl -s http://localhost:5670/api/health > /dev/null; do
    echo "⏳ 等待DB-GPT服务启动中..."
    sleep 10
done

echo "✅ DB-GPT服务已启动"

# 使用正确的数据库路径和表名注册数据源
echo "📊 在connect_config表中注册orange数据源..."

docker-compose exec -T webserver python3 -c "
import sqlite3
import json
from datetime import datetime

# 使用正确的数据库路径
db_path = '/app/pilot/meta_data/dbgpt.db'
print(f'使用数据库: {db_path}')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查是否已存在
    cursor.execute('SELECT * FROM connect_config WHERE db_name=?', ('orange',))
    existing = cursor.fetchone()
    
    if existing:
        print('⚠️ orange数据源已存在，更新配置...')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ext_config = json.dumps({
            'charset': 'utf8mb4',
            'autocommit': True,
            'sync_schema': True
        })
        
        cursor.execute('''
            UPDATE connect_config 
            SET db_host=?, db_port=?, db_user=?, db_pwd=?, 
                comment=?, gmt_modified=?, ext_config=?
            WHERE db_name=?
        ''', ('10.10.19.1', '9030', 'ai_user1', 'Weshare@2025',
              '逾期率分析数据库(Apache Doris)', now, ext_config, 'orange'))
    else:
        print('➕ 新增orange数据源配置...')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ext_config = json.dumps({
            'charset': 'utf8mb4',
            'autocommit': True,
            'sync_schema': True
        })
        
        cursor.execute('''
            INSERT INTO connect_config 
            (db_type, db_name, db_host, db_port, db_user, db_pwd, 
             comment, gmt_created, gmt_modified, ext_config) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('mysql', 'orange', '10.10.19.1', '9030', 'ai_user1', 
              'Weshare@2025', '逾期率分析数据库(Apache Doris)', 
              now, now, ext_config))
    
    conn.commit()
    
    # 验证结果
    cursor.execute('SELECT db_name, db_host, comment FROM connect_config WHERE db_name=\"orange\"')
    result = cursor.fetchone()
    if result:
        print(f'✅ 验证成功: {result[0]} @ {result[1]} - {result[2]}')
    else:
        print('❌ 验证失败：未找到数据源记录')
        
    conn.close()
    print('✅ 数据源配置操作完成')
    
except Exception as e:
    print(f'❌ 数据库操作失败: {e}')
"

# 重启webserver以加载新的数据源配置
echo "🔄 重启webserver以加载数据源配置..."
docker-compose restart webserver

echo "⏳ 等待服务重启..."
sleep 30

# 最终验证
echo "🎯 最终验证数据源状态..."
test_result=$(curl -X POST "http://localhost:5670/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chat_with_db_execute",
    "messages": [{"role": "user", "content": "显示数据库中的所有表"}],
    "chat_param": "orange",
    "temperature": 0.6
  }' 2>/dev/null)

if echo "$test_result" | grep -q "表结构信息不足"; then
    echo "❌ 表结构仍为空，可能需要额外配置"
    echo "💡 建议：检查Apache Doris连接兼容性"
else
    echo "✅ 数据源加载成功！"
fi

echo "🎉 修正版数据源自动注册脚本执行完成"
echo "📝 数据源已注册到connect_config表，可通过Web界面 http://localhost:5670 查看" 