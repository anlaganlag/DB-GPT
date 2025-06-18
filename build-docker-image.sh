#!/bin/bash

# DB-GPT 定制版本镜像构建脚本
# Custom DB-GPT Docker Image Build Script

set -e

# 配置变量
IMAGE_NAME="weshare/dbgpt-custom"
VERSION="1.0.0"
DOCKERFILE="Dockerfile.custom"

echo "🚀 开始构建 DB-GPT 定制版本 Docker 镜像..."
echo "📦 镜像名称: ${IMAGE_NAME}:${VERSION}"
echo "📝 Dockerfile: ${DOCKERFILE}"
echo ""

# 检查Dockerfile是否存在
if [ ! -f "${DOCKERFILE}" ]; then
    echo "❌ 错误: ${DOCKERFILE} 文件不存在"
    exit 1
fi

# 显示当前修改的关键文件
echo "📋 包含的关键定制文件:"
echo "   ✅ packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/sql_fixer.py (SQL修复器)"
echo "   ✅ packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/out_parser.py (输出解析器)"
echo "   ✅ packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/data_driven_analyzer.py (数据驱动分析器)"
echo "   ✅ configs/dbgpt-overdue-analysis.toml (逾期率分析配置)"
echo ""

# 构建镜像
echo "🔨 正在构建 Docker 镜像..."
docker build \
    -f ${DOCKERFILE} \
    -t ${IMAGE_NAME}:${VERSION} \
    -t ${IMAGE_NAME}:latest \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Docker 镜像构建成功!"
    echo ""
    echo "📋 镜像信息:"
    docker images | grep "${IMAGE_NAME}" | head -2
    echo ""
    echo "🎯 功能特性:"
    echo "   ✅ SQL自动修复 (DATE_ROUND, create_time, 中文别名等)"
    echo "   ✅ 数据驱动分析报告生成"
    echo "   ✅ Doris数据库兼容性"
    echo "   ✅ 模板生成明显标记"
    echo "   ✅ 智能错误处理"
    echo ""
    echo "🚀 运行命令:"
    echo "   docker run -d --name dbgpt-custom \\"
    echo "     -p 5670:5670 \\"
    echo "     -e SILICONFLOW_API_KEY=your_api_key \\"
    echo "     ${IMAGE_NAME}:${VERSION}"
    echo ""
    echo "📦 保存镜像到文件:"
    echo "   docker save ${IMAGE_NAME}:${VERSION} | gzip > dbgpt-custom-${VERSION}.tar.gz"
    echo ""
    echo "📥 从文件加载镜像:"
    echo "   gunzip -c dbgpt-custom-${VERSION}.tar.gz | docker load"
else
    echo "❌ Docker 镜像构建失败!"
    exit 1
fi 