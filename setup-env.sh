#!/bin/bash

# 环境变量设置脚本
# 用于配置Chrome和Puppeteer相关环境变量

echo "🔧 环境变量设置工具"
echo "===================="

# 检查Chrome是否安装
CHROME_PATH=""
if command -v google-chrome &> /dev/null; then
    CHROME_PATH="/usr/bin/google-chrome"
elif command -v chromium-browser &> /dev/null; then
    CHROME_PATH="/usr/bin/chromium-browser"
elif command -v google-chrome-stable &> /dev/null; then
    CHROME_PATH="/usr/bin/google-chrome-stable"
else
    echo "❌ 错误: 未找到Chrome浏览器"
    echo "请先安装Chrome: sudo apt install google-chrome-stable"
    exit 1
fi

echo "✅ 找到Chrome: $CHROME_PATH"

# 检查配置文件
SHELL_CONFIG=""
if [ -f ~/.bashrc ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -f ~/.zshrc ]; then
    SHELL_CONFIG="$HOME/.zshrc"
else
    echo "❌ 未找到shell配置文件"
    exit 1
fi

echo "📝 使用配置文件: $SHELL_CONFIG"

# 检查是否已经设置过环境变量
if grep -q "CHROME_BIN" "$SHELL_CONFIG"; then
    echo "⚠️  环境变量已存在，是否要重新设置？(y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "取消设置"
        exit 0
    fi
    
    # 备份配置文件
    cp "$SHELL_CONFIG" "${SHELL_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📦 已备份配置文件"
    
    # 移除旧的环境变量设置
    sed -i '/# Chrome环境变量设置/,+3d' "$SHELL_CONFIG"
    echo "🧹 已清理旧的环境变量"
fi

# 添加新的环境变量
echo "" >> "$SHELL_CONFIG"
echo "# Chrome环境变量设置 (用于Markdown转PDF)" >> "$SHELL_CONFIG"
echo "export CHROME_BIN=$CHROME_PATH" >> "$SHELL_CONFIG"
echo "export PUPPETEER_EXECUTABLE_PATH=$CHROME_PATH" >> "$SHELL_CONFIG"
echo "export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true" >> "$SHELL_CONFIG"

echo "✅ 环境变量已添加到 $SHELL_CONFIG"

# 重新加载配置
source "$SHELL_CONFIG"
echo "🔄 已重新加载配置文件"

# 验证设置
echo ""
echo "🔍 验证环境变量设置:"
echo "   CHROME_BIN: $CHROME_BIN"
echo "   PUPPETEER_EXECUTABLE_PATH: $PUPPETEER_EXECUTABLE_PATH"
echo "   PUPPETEER_SKIP_CHROMIUM_DOWNLOAD: $PUPPETEER_SKIP_CHROMIUM_DOWNLOAD"

echo ""
echo "✅ 环境变量设置完成!"
echo "💡 提示: 重新打开终端或运行 'source $SHELL_CONFIG' 使设置生效" 