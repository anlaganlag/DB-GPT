# VSCode Markdown-Preview-Enhanced PDF导出问题解决指南

## 问题诊断

### 常见错误类型
1. **Chrome executable path is not set**
2. **Chrome failed to start**
3. **Permission denied**
4. **Timeout error**

## 解决方案

### 方案1: 配置Chrome路径

1. 打开VSCode设置 (Ctrl+,)
2. 搜索 "markdown-preview-enhanced"
3. 找到 "Chrome Path" 设置项
4. 设置为: `/usr/bin/google-chrome`

或者直接编辑settings.json:
```json
{
    "markdown-preview-enhanced.chromePath": "/usr/bin/google-chrome"
}
```

### 方案2: 安装Puppeteer (推荐)

在项目目录下安装Puppeteer:
```bash
npm install -g puppeteer
# 或者
npm install puppeteer
```

### 方案3: 使用系统Chrome启动参数

创建Chrome启动脚本:
```bash
#!/bin/bash
# 文件名: chrome-headless.sh
/usr/bin/google-chrome --headless --disable-gpu --no-sandbox --disable-dev-shm-usage "$@"
```

然后在VSCode设置中指向这个脚本。

### 方案4: 安装缺失依赖

```bash
# 安装Chrome依赖
sudo apt-get update
sudo apt-get install -y \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxss1 \
    libxtst6 \
    xdg-utils

# 安装中文字体支持
sudo apt-get install -y fonts-wqy-zenhei fonts-wqy-microhei
```

### 方案5: 使用Pandoc替代方案

安装Pandoc:
```bash
sudo apt-get install pandoc texlive-xetex
```

然后可以使用命令行转换:
```bash
pandoc POC_Feasibility_Report_zh.md -o POC_Feasibility_Report_zh.pdf --pdf-engine=xelatex
```

## 测试步骤

1. 重启VSCode
2. 打开markdown文件
3. 右键选择 "Markdown Preview Enhanced: Open Preview"
4. 在预览窗口右键选择 "Chrome (Puppeteer) > PDF"

## 高级配置

### PDF导出质量优化
在VSCode设置中添加:
```json
{
    "markdown-preview-enhanced.puppeteerArgs": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu"
    ],
    "markdown-preview-enhanced.printBackground": true,
    "markdown-preview-enhanced.puppeteerWaitForTimeout": 3000
}
```

### 自定义CSS样式
创建 `.markdown-preview-enhanced/style.less` 文件:
```less
.markdown-preview.markdown-preview {
  // PDF专用样式
  @media print {
    .pagebreak { page-break-before: always; }
    h1 { color: #d73527 !important; }
    h2 { color: #1f4e79 !important; }
    h3 { color: #7030a0 !important; }
  }
}
```

## 故障排除

### 如果仍然失败，尝试以下步骤：

1. **检查Chrome是否能正常启动**:
   ```bash
   google-chrome --headless --disable-gpu --dump-dom https://www.google.com
   ```

2. **检查VSCode插件日志**:
   - 打开VSCode开发者工具 (Help > Toggle Developer Tools)
   - 查看Console中的错误信息

3. **临时解决方案 - 使用浏览器打印**:
   - 在预览窗口中右键选择 "Open in Browser"
   - 在浏览器中使用 Ctrl+P 打印为PDF

4. **使用我们之前创建的脚本**:
   ```bash
   ./export-pdf.sh POC_Feasibility_Report_zh.md
   ```

## 推荐配置

最终推荐的VSCode settings.json配置:
```json
{
    "markdown-preview-enhanced.chromePath": "/usr/bin/google-chrome",
    "markdown-preview-enhanced.puppeteerArgs": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions"
    ],
    "markdown-preview-enhanced.printBackground": true,
    "markdown-preview-enhanced.puppeteerWaitForTimeout": 5000,
    "markdown-preview-enhanced.enableScriptExecution": true
}
``` 