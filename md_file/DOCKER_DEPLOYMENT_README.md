# DB-GPT 定制版本 Docker 部署指南

## 🎯 项目简介

这是一个定制增强的DB-GPT版本，包含以下特性：

- ✅ **SQL自动修复功能** - 自动修复DATE_ROUND、create_time、中文别名等兼容性问题
- ✅ **数据驱动分析报告** - 基于真实SQL执行结果生成分析报告
- ✅ **Doris数据库完全兼容** - 专门针对Apache Doris优化
- ✅ **模板内容明显标记** - 清晰区分模板生成和数据驱动内容
- ✅ **智能错误处理** - 多层SQL修复策略

## 🚀 快速开始

### 方法1: 使用预构建镜像 (推荐)

如果您已经有构建好的镜像文件：

```bash
# 1. 加载镜像
gunzip -c dbgpt-custom-1.0.0.tar.gz | docker load

# 2. 创建环境变量文件
cat > .env << 'EOF'
SILICONFLOW_API_KEY=sk-your-actual-api-key
BUSINESS_MYSQL_HOST=10.10.19.1
BUSINESS_MYSQL_PORT=9030
BUSINESS_MYSQL_DATABASE=orange
BUSINESS_MYSQL_USER=ai_user1
BUSINESS_MYSQL_PASSWORD=Weshare@2025
EOF

# 3. 启动服务
docker-compose -f docker-compose.custom.yml up -d
```

### 方法2: 从源码构建

如果您需要重新构建镜像：

```bash
# 1. 给构建脚本执行权限
chmod +x build-docker-image.sh

# 2. 构建镜像
./build-docker-image.sh

# 3. 创建环境配置并启动
# (同方法1的步骤2-3)
```

## 📋 环境变量配置

创建 `.env` 文件并配置以下变量：

```bash
# 必填配置
SILICONFLOW_API_KEY=sk-your-siliconflow-api-key

# 业务数据库配置
BUSINESS_MYSQL_HOST=your-database-host
BUSINESS_MYSQL_PORT=your-database-port
BUSINESS_MYSQL_DATABASE=your-database-name
BUSINESS_MYSQL_USER=your-database-user
BUSINESS_MYSQL_PASSWORD=your-database-password

# 可选配置
MODELS_PATH=./models
DBGPT_LANG=zh
```

## 🔧 详细部署步骤

### 步骤1: 准备环境

```bash
# 确保Docker和Docker Compose已安装
docker --version
docker-compose --version

# 创建工作目录
mkdir dbgpt-custom-deployment
cd dbgpt-custom-deployment
```

### 步骤2: 获取部署文件

将以下文件复制到工作目录：
- `docker-compose.custom.yml`
- `dbgpt-custom-1.0.0.tar.gz` (镜像文件)
- 配置文件目录 `configs/`

### 步骤3: 加载Docker镜像

```bash
# 加载镜像文件
gunzip -c dbgpt-custom-1.0.0.tar.gz | docker load

# 验证镜像已加载
docker images | grep weshare/dbgpt-custom
```

### 步骤4: 配置环境变量

```bash
# 创建环境变量文件
cat > .env << 'EOF'
# SiliconFlow API配置
SILICONFLOW_API_KEY=sk-your-actual-siliconflow-api-key

# 业务数据库配置
BUSINESS_MYSQL_HOST=10.10.19.1
BUSINESS_MYSQL_PORT=9030
BUSINESS_MYSQL_DATABASE=orange
BUSINESS_MYSQL_USER=ai_user1
BUSINESS_MYSQL_PASSWORD=Weshare@2025

# 可选配置
MODELS_PATH=./models
DBGPT_LANG=zh
EOF
```

### 步骤5: 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.custom.yml up -d

# 查看服务状态
docker-compose -f docker-compose.custom.yml ps

# 查看日志
docker-compose -f docker-compose.custom.yml logs -f dbgpt-webserver
```

## 📊 验证部署

### 检查服务状态

```bash
# 检查容器运行状态
docker ps

# 检查健康状态
docker-compose -f docker-compose.custom.yml ps

# 访问Web界面
curl http://localhost:5670/api/health
```

### 访问应用

- **Web界面**: http://localhost:5670
- **API文档**: http://localhost:5670/docs
- **健康检查**: http://localhost:5670/api/health

## 🛠️ 高级配置

### 自定义配置文件

如果需要修改配置，可以编辑 `configs/dbgpt-overdue-analysis.toml`：

```toml
[system]
language = "zh"

[service.web]
host = "0.0.0.0"
port = 5670

# 模型配置
[[models.llms]]
name = "Qwen/Qwen2.5-Coder-32B-Instruct"
provider = "proxy/siliconflow"
api_key = "your-api-key"
```

### 本地模型支持

如果需要使用本地模型：

```bash
# 创建模型目录
mkdir -p ./models

# 设置环境变量
echo "MODELS_PATH=./models" >> .env

# 重启服务
docker-compose -f docker-compose.custom.yml restart
```

## 🔍 故障排除

### 常见问题

1. **API Key错误**
   ```bash
   # 检查环境变量
   docker-compose -f docker-compose.custom.yml exec dbgpt-webserver env | grep SILICONFLOW
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库配置
   docker-compose -f docker-compose.custom.yml logs dbgpt-mysql
   ```

3. **端口占用**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep 5670
   
   # 修改端口映射
   # 编辑 docker-compose.custom.yml 中的 ports 配置
   ```

### 查看日志

```bash
# 查看所有服务日志
docker-compose -f docker-compose.custom.yml logs

# 查看特定服务日志
docker-compose -f docker-compose.custom.yml logs -f dbgpt-webserver

# 查看实时日志
docker-compose -f docker-compose.custom.yml logs -f --tail=100
```

## 🔄 更新和维护

### 更新镜像

```bash
# 停止服务
docker-compose -f docker-compose.custom.yml down

# 加载新镜像
gunzip -c dbgpt-custom-new-version.tar.gz | docker load

# 更新镜像标签
docker tag weshare/dbgpt-custom:new-version weshare/dbgpt-custom:latest

# 重启服务
docker-compose -f docker-compose.custom.yml up -d
```

### 数据备份

```bash
# 备份持久化数据
docker run --rm \
  -v dbgpt-custom-deployment_dbgpt_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/dbgpt-data-backup.tar.gz /data

# 备份数据库
docker-compose -f docker-compose.custom.yml exec dbgpt-mysql \
  mysqldump -u dbgpt_user -pdbgpt_pass_123 dbgpt > dbgpt-db-backup.sql
```

## 📞 技术支持

如果遇到问题，请检查：

1. **系统要求**: Docker 20.10+, Docker Compose 2.0+
2. **内存要求**: 至少 4GB RAM
3. **磁盘空间**: 至少 10GB 可用空间
4. **网络**: 确保可以访问 SiliconFlow API

## 🎉 功能特性说明

### SQL自动修复

系统会自动修复以下SQL兼容性问题：
- `DATE_ROUND` 函数 → 自动移除
- `create_time` 字段 → 自动转换为 `createtime`
- 中文别名格式 → 自动添加正确的反引号
- `FORMAT` 函数 → 自动替换为 `ROUND`

### 数据驱动分析

当SQL包含以下关键词时，自动触发数据驱动分析：
- `mob`, `overdue`, `group by`, `count`, `sum`, `avg`

### 模板内容标记

所有模板生成的内容都会有明显标记：
- 🚨 **[模板生成]** - 报告标题
- ⚠️ **[模板内容]** - 关键发现
- ⚠️ **[模板洞察]** - 业务洞察
- ⚠️ **[模板建议]** - 建议事项

这样您可以清楚地区分哪些是基于真实数据的分析，哪些是模板生成的内容。 