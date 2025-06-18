# VSCode Markdown-Preview-Enhanced PDF导出问题解决方案

## 🎯 问题分析

VSCode的markdown-preview-enhanced插件导出PDF时常见的错误包括：
- `Chrome executable path is not set`
- `Chrome failed to start`
- `Permission denied`
- `Timeout error`

## ✅ 已完成的修复

### 1. Chrome路径配置
- ✅ 检测到Chrome路径: `/usr/bin/google-chrome`
- ✅ 已添加到VSCode配置中

### 2. VSCode设置更新
已更新的配置文件: `~/.config/Code/User/settings.json`
```json
{
    "markdown-preview-enhanced.chromePath": "/usr/bin/google-chrome",
    "markdown-preview-enhanced.puppeteerArgs": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-dev-tools"
    ],
    "markdown-preview-enhanced.printBackground": true,
    "markdown-preview-enhanced.puppeteerWaitForTimeout": 5000,
    "markdown-preview-enhanced.enableScriptExecution": true
}
```

### 3. Puppeteer安装
- ✅ 本地安装完成 (项目目录下)
- ⚠️ 全局安装因权限问题跳过 (不影响功能)

### 4. 测试文件
- ✅ 创建了 `test_markdown_pdf.md` 测试文件

## 🚀 使用步骤

1. **重启VSCode** (重要！)
2. 打开任意markdown文件 (如 `test_markdown_pdf.md`)
3. 右键选择 `Markdown Preview Enhanced: Open Preview`
4. 在预览窗口右键选择 `Chrome (Puppeteer) > PDF`
5. 等待PDF生成完成

## 🔧 如果仍然有问题

### 方案A: 检查插件状态
- 确保markdown-preview-enhanced插件已启用
- 在VSCode扩展页面重新安装插件

### 方案B: 查看错误日志
- 按F12打开VSCode开发者工具
- 查看Console中的具体错误信息

### 方案C: 使用备用脚本
如果VSCode插件仍有问题，使用我们的备用脚本：
```bash
./export-pdf.sh POC_Feasibility_Report_zh.md
```

### 方案D: 浏览器打印
1. 在预览窗口右键选择 "Open in Browser"
2. 在浏览器中按Ctrl+P，选择"另存为PDF"

## 📋 系统状态检查

- ✅ Chrome浏览器: `/usr/bin/google-chrome` (版本 137.0.7151.119)
- ✅ Chrome headless模式: 正常工作
- ✅ VSCode配置: 已更新
- ✅ Puppeteer: 已安装 (本地)
- ✅ 测试文件: 已创建

## 🎉 预期结果

配置完成后，您应该能够：
- 在VSCode中直接导出markdown为PDF
- 支持中文字体显示
- 支持彩色输出
- 支持表格、代码块等复杂格式

## 💡 小贴士

- 如果PDF导出很慢，可以调整 `puppeteerWaitForTimeout` 参数
- 如果需要自定义PDF样式，可以创建 `.markdown-preview-enhanced/style.less` 文件
- 建议在导出前先在预览窗口检查格式是否正确

---

**配置时间**: 2025-06-18
**Chrome版本**: 137.0.7151.119
**VSCode版本**: 1.100.3
**插件版本**: shd101wyy.markdown-preview-enhanced-0.8.18 截图 2025-06-18 13-34-57.png