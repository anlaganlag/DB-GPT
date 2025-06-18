#!/bin/bash
echo "🚀 DB-GPT 定制版本快速启动脚本"
echo ""

# 检查文件
if [ ! -f "dbgpt-custom-1.0.0.tar.gz" ]; then
    echo "❌ 错误: 镜像文件 dbgpt-custom-1.0.0.tar.gz 不存在"
    exit 1
fi

# 加载镜像
echo "📦 正在加载 Docker 镜像..."
gunzip -c dbgpt-custom-1.0.0.tar.gz | docker load

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  创建环境变量配置文件 .env"
    cat > .env << 'ENVEOF'
# 必填: SiliconFlow API Key
SILICONFLOW_API_KEY=sk-your-siliconflow-api-key

# 业务数据库配置
BUSINESS_MYSQL_HOST=10.10.19.1
BUSINESS_MYSQL_PORT=9030
BUSINESS_MYSQL_DATABASE=orange
BUSINESS_MYSQL_USER=ai_user1
BUSINESS_MYSQL_PASSWORD=Weshare@2025

# 可选配置
MODELS_PATH=./models
DBGPT_LANG=zh
ENVEOF
    echo "📝 请编辑 .env 文件，填入正确的配置信息"
    echo "⏸️  脚本暂停，请配置完成后按任意键继续..."
    read -n 1
fi

# 启动服务
echo "🚀 正在启动服务..."
docker-compose -f docker-compose.custom.yml up -d

echo ""
echo "✅ 启动完成!"
echo "🌐 访问地址: http://localhost:5670"
echo ""
echo "📊 查看状态: docker-compose -f docker-compose.custom.yml ps"
echo "📋 查看日志: docker-compose -f docker-compose.custom.yml logs -f"
