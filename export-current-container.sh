#!/bin/bash

# 从当前运行的容器创建定制镜像
# Export Custom DB-GPT Image from Running Container

set -e

# 配置变量
CONTAINER_NAME="db-gpt_webserver_1"  # 当前运行的容器名称
EXPORT_IMAGE_NAME="weshare/dbgpt-custom"
VERSION="1.0.0"
EXPORT_FILE="dbgpt-custom-${VERSION}.tar.gz"

echo "🚀 开始从运行中的容器创建定制镜像..."
echo "📦 容器名称: ${CONTAINER_NAME}"
echo "🎯 目标镜像: ${EXPORT_IMAGE_NAME}:${VERSION}"
echo ""

# 检查容器是否存在
if ! docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ 错误: 容器 ${CONTAINER_NAME} 不存在"
    echo "📋 当前运行的容器:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    exit 1
fi

# 检查容器是否运行
if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠️  警告: 容器 ${CONTAINER_NAME} 未运行，将使用最后状态"
fi

echo "📋 当前容器状态:"
docker ps -a --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 创建定制镜像
echo "🔄 正在从容器创建镜像..."
docker commit \
    --author "weshare <weshare@example.com>" \
    --message "DB-GPT Custom Version with SQL Fixer and Data-Driven Analysis" \
    --change 'LABEL version="1.0.0"' \
    --change 'LABEL description="DB-GPT Custom Version with Enhanced SQL Fixing and Data-Driven Analysis"' \
    --change 'EXPOSE 5670' \
    ${CONTAINER_NAME} \
    ${EXPORT_IMAGE_NAME}:${VERSION}

if [ $? -eq 0 ]; then
    echo "✅ 镜像创建成功!"
    
    # 同时创建latest标签
    docker tag ${EXPORT_IMAGE_NAME}:${VERSION} ${EXPORT_IMAGE_NAME}:latest
    
    echo ""
    echo "📋 镜像信息:"
    docker images | grep "${EXPORT_IMAGE_NAME}" | head -2
    echo ""
    
    # 导出镜像到文件
    echo "📦 正在导出镜像到文件: ${EXPORT_FILE}"
    docker save ${EXPORT_IMAGE_NAME}:${VERSION} | gzip > ${EXPORT_FILE}
    
    if [ $? -eq 0 ]; then
        echo "✅ 镜像导出成功!"
        echo ""
        echo "📊 文件信息:"
        ls -lh ${EXPORT_FILE}
        echo ""
        echo "🎯 定制功能特性:"
        echo "   ✅ SQL自动修复 (DATE_ROUND, create_time, 中文别名, FORMAT函数)"
        echo "   ✅ 数据驱动分析报告生成"
        echo "   ✅ Doris数据库完全兼容"
        echo "   ✅ 模板生成内容明显标记"
        echo "   ✅ 智能错误处理和修复"
        echo ""
        echo "🚀 使用说明:"
        echo "   1. 在新环境中加载镜像:"
        echo "      gunzip -c ${EXPORT_FILE} | docker load"
        echo ""
        echo "   2. 创建环境配置文件 .env:"
        echo "      SILICONFLOW_API_KEY=sk-your-api-key"
        echo "      BUSINESS_MYSQL_HOST=your-database-host"
        echo "      BUSINESS_MYSQL_PORT=your-database-port"
        echo "      BUSINESS_MYSQL_DATABASE=your-database-name"
        echo "      BUSINESS_MYSQL_USER=your-database-user"
        echo "      BUSINESS_MYSQL_PASSWORD=your-database-password"
        echo ""
        echo "   3. 使用docker-compose启动:"
        echo "      docker-compose -f docker-compose.custom.yml up -d"
        echo ""
        echo "   4. 或者直接运行:"
        echo "      docker run -d --name dbgpt-custom \\"
        echo "        -p 5670:5670 \\"
        echo "        -e SILICONFLOW_API_KEY=your-api-key \\"
        echo "        ${EXPORT_IMAGE_NAME}:${VERSION}"
        
        # 创建导出包
        echo ""
        echo "📦 创建完整部署包..."
        mkdir -p dbgpt-deployment-package
        cp ${EXPORT_FILE} dbgpt-deployment-package/
        cp docker-compose.custom.yml dbgpt-deployment-package/
        cp DOCKER_DEPLOYMENT_README.md dbgpt-deployment-package/
        cp -r configs dbgpt-deployment-package/
        
        # 创建快速启动脚本
        cat > dbgpt-deployment-package/quick-start.sh << 'EOF'
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
EOF

        chmod +x dbgpt-deployment-package/quick-start.sh
        
        # 打包部署包
        tar -czf dbgpt-deployment-package.tar.gz dbgpt-deployment-package/
        
        echo ""
        echo "📦 完整部署包创建成功: dbgpt-deployment-package.tar.gz"
        echo "📋 包含文件:"
        echo "   ✅ ${EXPORT_FILE} (Docker镜像)"
        echo "   ✅ docker-compose.custom.yml (Docker编排配置)"
        echo "   ✅ DOCKER_DEPLOYMENT_README.md (详细部署文档)"
        echo "   ✅ quick-start.sh (快速启动脚本)"
        echo "   ✅ configs/ (配置文件目录)"
        echo ""
        echo "🎉 打包完成！您可以将 dbgpt-deployment-package.tar.gz 传输到任何支持Docker的环境中部署。"
        
    else
        echo "❌ 镜像导出失败!"
        exit 1
    fi
else
    echo "❌ 镜像创建失败!"
    exit 1
fi 