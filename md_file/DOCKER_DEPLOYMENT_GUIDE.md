# DB-GPT Enhanced Docker 部署指南

## 🎉 镜像推送成功！

您的增强版DB-GPT镜像已成功推送到Docker Hub：

**镜像地址**: `jb140313/dbgpt-enhanced:latest`

## 📦 镜像信息

- **Docker Hub用户**: jb140313
- **镜像名称**: dbgpt-enhanced
- **标签**: latest
- **镜像大小**: 1.36GB
- **推送时间**: 刚刚完成

## 🚀 快速部署

### 方法1: 直接运行容器

```bash
# 拉取镜像
docker pull jb140313/dbgpt-enhanced:latest

# 运行容器
docker run -d \
  --name dbgpt-enhanced \
  -p 5670:5670 \
  -e OPENAI_API_KEY=your_openai_api_key \
  -e OPENAI_API_BASE=your_openai_api_base \
  jb140313/dbgpt-enhanced:latest
```

### 方法2: 使用Docker Compose

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  dbgpt-enhanced:
    image: jb140313/dbgpt-enhanced:latest
    container_name: dbgpt-enhanced
    ports:
      - "5670:5670"
    environment:
      - OPENAI_API_KEY=your_openai_api_key
      - OPENAI_API_BASE=your_openai_api_base
    volumes:
      - ./data:/app/pilot/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5670/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

然后运行：

```bash
docker-compose up -d
```

## 🔧 环境变量配置

| 变量名 | 描述 | 示例值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | `sk-xxx...` |
| `OPENAI_API_BASE` | OpenAI API基础URL | `https://api.openai.com/v1` |
| `DB_USER` | 数据库用户名 | `root` |
| `DB_PASSWORD` | 数据库密码 | `aa123456` |
| `DB_HOST` | 数据库主机 | `localhost` |
| `DB_PORT` | 数据库端口 | `3306` |

## 📋 功能特性

此增强版镜像包含以下改进：

### ✅ 已修复的问题
- 修复了 `overdue_rate_stats` 表缺失问题
- 完善了SQL错误显示机制
- 改进了表格格式显示
- 增加了SQL语句显示功能
- 实现了双模式输出（简单/增强）

### 🎯 核心功能
- **智能SQL错误处理**: 显示详细错误信息而非通用错误
- **专业表格格式**: Markdown格式的清晰表格显示
- **SQL语句展示**: 查询结果旁显示对应SQL代码
- **双模式输出**: 支持简单模式（默认）和增强模式
- **业务术语解释**: 自动添加MOB、逾期率等术语说明

## 🌐 访问应用

容器启动后，访问以下地址：

- **Web界面**: http://localhost:5670
- **API文档**: http://localhost:5670/docs
- **健康检查**: http://localhost:5670/health

## 🔍 故障排除

### 查看容器日志
```bash
docker logs dbgpt-enhanced
```

### 进入容器调试
```bash
docker exec -it dbgpt-enhanced bash
```

### 重启容器
```bash
docker restart dbgpt-enhanced
```

## 📊 性能监控

### 查看容器状态
```bash
docker stats dbgpt-enhanced
```

### 查看容器详情
```bash
docker inspect dbgpt-enhanced
```

## 🔄 更新镜像

```bash
# 停止当前容器
docker stop dbgpt-enhanced

# 删除当前容器
docker rm dbgpt-enhanced

# 拉取最新镜像
docker pull jb140313/dbgpt-enhanced:latest

# 重新运行容器
docker run -d --name dbgpt-enhanced -p 5670:5670 jb140313/dbgpt-enhanced:latest
```

## 📞 技术支持

如果遇到问题，请检查：

1. **Docker是否正常运行**
2. **端口5670是否被占用**
3. **环境变量是否正确配置**
4. **网络连接是否正常**

## 🎯 下一步

1. 在目标服务器上拉取镜像
2. 配置环境变量
3. 启动容器
4. 访问Web界面测试功能
5. 验证逾期率分析等核心功能

---

**镜像推送完成时间**: $(Get-Date)
**推送状态**: ✅ 成功
**镜像地址**: `jb140313/dbgpt-enhanced:latest` 