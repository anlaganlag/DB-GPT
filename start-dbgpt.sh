#!/bin/bash

# DB-GPT 项目启动脚本
# 使用方法: ./start-dbgpt.sh

echo "🚀 开始启动 DB-GPT 项目..."

# 1. 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 2. 进入项目目录
cd /home/weshare/DB-GPT

# 3. 显示当前状态
echo "📋 检查当前容器状态..."
docker ps

# 4. 询问是否需要清理
echo ""
read -p "是否需要清理旧容器和数据？(建议首次启动或遇到问题时选择y) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理旧容器和数据卷..."
    docker-compose down -v
fi

# 5. 启动所有服务
echo "🔧 启动所有服务..."
docker-compose up -d

# 6. 等待服务启动
echo "⏳ 等待服务启动 (45秒)..."
for i in {1..45}; do
    printf "."
    sleep 1
done
echo ""

# 7. 检查服务状态
echo "📊 检查服务状态..."
docker ps

# 8. 测试Web界面
echo ""
echo "🌐 测试Web界面访问..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5670)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Web界面正常访问 (HTTP $HTTP_CODE)"
    echo ""
    echo "🎉 DB-GPT 项目启动成功！"
    echo "📱 Web界面地址: http://localhost:5670"
    echo "🗄️  MySQL端口: localhost:3307"
    echo ""
    echo "💡 现在可以在Web界面中进行逾期率分析查询了！"
else
    echo "❌ Web界面访问失败 (HTTP $HTTP_CODE)"
    echo "📋 webserver日志:"
    docker-compose logs --tail=10 webserver
fi 