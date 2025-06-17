#!/bin/bash

# Docker容器启动时自动执行的数据源配置脚本
# 这个脚本会在webserver容器内部运行

echo "🚀 启动数据源自动配置..."

# 等待SQLite数据库文件创建
while [ ! -f "/app/pilot/data/dbgpt.db" ]; do
    echo "⏳ 等待系统数据库初始化..."
    sleep 5
done

sleep 10  # 等待数据库完全初始化

# 检查并配置orange数据源
echo "🔧 配置orange数据源..."

# 检查是否已存在配置
EXISTING=$(sqlite3 /app/pilot/data/dbgpt.db "SELECT COUNT(*) FROM connect_config WHERE db_name='orange';" 2>/dev/null || echo "0")

if [ "$EXISTING" = "0" ]; then
    echo "📝 创建orange数据源配置..."
    sqlite3 /app/pilot/data/dbgpt.db "
    INSERT INTO connect_config (
        db_name, db_type, db_host, db_port, 
        db_user, db_pwd, db_path, comment
    ) VALUES (
        'orange', 'mysql', '10.10.19.1', 9030,
        'ai_user1', 'Weshare@2025', 'orange', 
        '逾期率分析数据库(Apache Doris伪装成MySQL)'
    );
    " 2>/dev/null
    echo "✅ orange数据源配置已创建"
else
    echo "🔧 检查和修复现有配置..."
    
    # 确保所有字段都正确
    sqlite3 /app/pilot/data/dbgpt.db "
    UPDATE connect_config SET 
        db_type='mysql',
        db_host='10.10.19.1',
        db_port=9030,
        db_user='ai_user1',
        db_pwd='Weshare@2025',
        db_path='orange'
    WHERE db_name='orange';
    " 2>/dev/null
    echo "✅ orange数据源配置已修复"
fi

echo "🎉 数据源自动配置完成！" 