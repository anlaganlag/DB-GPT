#!/bin/bash

# Markdown转PDF导出脚本 (彩色增强版)
# 解决 "Chrome executable path is not set" 错误

echo "🚀 Markdown转PDF导出工具 (彩色增强版)"
echo "======================================="

# 检查参数
if [ $# -lt 1 ]; then
    echo "使用方法: ./export-pdf.sh <markdown文件> [输出文件名]"
    echo "示例: ./export-pdf.sh POC_Feasibility_Report_zh.md"
    echo "示例: ./export-pdf.sh POC_Feasibility_Report_zh.md 我的报告.pdf"
    echo ""
    echo "🎨 新功能: 彩色PDF输出"
    echo "   • 彩色标题 (红色H1, 蓝色H2, 紫色H3等)"
    echo "   • 渐变表格头部"
    echo "   • 彩色代码块"
    echo "   • 美化的引用块和链接"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${2:-$(basename "$INPUT_FILE" .md).pdf}"

# 检查输入文件是否存在
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ 错误: 文件 '$INPUT_FILE' 不存在"
    exit 1
fi

# 检查是否安装了Node.js和npm
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 需要安装Node.js"
    echo "请运行: sudo apt install nodejs npm"
    exit 1
fi

# 检查是否安装了Chrome
CHROME_PATH=""
if command -v google-chrome &> /dev/null; then
    CHROME_PATH="/usr/bin/google-chrome"
elif command -v chromium-browser &> /dev/null; then
    CHROME_PATH="/usr/bin/chromium-browser"
elif command -v google-chrome-stable &> /dev/null; then
    CHROME_PATH="/usr/bin/google-chrome-stable"
else
    echo "❌ 错误: 未找到Chrome浏览器"
    echo "请安装Chrome: sudo apt install google-chrome-stable"
    exit 1
fi

echo "✅ 找到Chrome: $CHROME_PATH"

# 检查并安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖包..."
    PUPPETEER_SKIP_DOWNLOAD=true npm install puppeteer marked
fi

# 使用Node.js脚本转换
echo "🔄 正在转换 '$INPUT_FILE' 为 '$OUTPUT_FILE'..."
echo "🎨 启用彩色模式: 标题、表格、代码块将显示彩色"
node markdown-to-pdf.js "$INPUT_FILE" "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✅ 转换成功!"
    echo "📄 PDF文件: $OUTPUT_FILE"
    echo "📊 文件大小: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo "🌈 彩色效果: 已启用 (标题、表格、代码块等显示彩色)"
else
    echo "❌ 转换失败"
    exit 1
fi 