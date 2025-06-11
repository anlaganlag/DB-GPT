# DB-GPT 逾期率分析项目启动指南

## 📋 启动前准备

### 系统要求
- **Ubuntu**: 18.04+ (推荐 20.04/22.04)
- **Windows**: 10/11 (可选)
- **内存**: 至少4GB可用内存
- **存储**: 至少10GB可用空间
- **端口**: 5670和3307未被占用

### 必需软件

#### Ubuntu系统
```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo apt install docker-compose -y

# 将当前用户添加到docker组（避免每次使用sudo）
sudo usermod -aG docker $USER

# 重新登录或执行以下命令使组权限生效
newgrp docker

# 验证安装
docker --version
docker-compose --version
```

#### Windows系统
- **Docker Desktop**: 从官网下载安装
- **PowerShell**: Windows自带

## 🚀 完整启动步骤

### Ubuntu系统启动步骤

#### 步骤1: 检查Docker服务

```bash
# 检查Docker服务状态
sudo systemctl status docker

# 如果Docker未运行，启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证Docker正常工作
docker run hello-world
```

#### 步骤2: 克隆或进入项目目录

```bash
# 如果是首次使用，克隆项目（示例）
# git clone <your-repo-url>
# cd DB-GPT

# 如果项目已存在，进入项目目录
cd /path/to/your/DB-GPT
```

#### 步骤3: 启动DB-GPT项目

```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

#### 步骤4: 验证服务启动

```bash
# 检查容器状态
docker ps

# 应该看到两个容器运行：
# - db-gpt-webserver-1 (端口5670)
# - db-gpt-db-1 (端口3307)

# 测试Web应用
curl -I http://localhost:5670

# 测试数据库连接
docker exec db-gpt-db-1 mysql -u root -paa123456 -e "SHOW DATABASES;"
```

### Windows系统启动步骤

#### 步骤1: 启动Docker Desktop

```powershell
# 检查Docker Desktop状态
docker version

# 如果Docker未运行，启动Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 等待Docker Desktop完全启动（通常需要1-2分钟）
Start-Sleep -Seconds 60
```

#### 步骤2: 启动DB-GPT项目

```powershell
# 进入项目目录
cd D:\path\to\your\DB-GPT

# 启动所有服务
docker-compose up -d

# 验证容器状态
docker ps
```

#### 步骤3: 验证服务启动

```powershell
# 测试Web应用
curl -I http://localhost:5670

# 测试数据库连接
docker exec db-gpt-db-1 mysql -u root -paa123456 -e "SHOW DATABASES;"
```

## ✅ 启动成功标志

当您看到以下状态时，项目已成功启动：

- ✅ **Docker服务**: 运行中
- ✅ **Web服务器**: http://localhost:5670 可访问
- ✅ **数据库服务**: MySQL在端口3307运行
- ✅ **数据库内容**: 包含 `dbgpt` 和 `overdue_analysis` 数据库

## 🔗 开始使用

### 访问应用

1. **打开浏览器**，访问：
   ```
   http://localhost:5670
   ```

2. **进入聊天界面**：
   - 点击聊天或对话选项
   - 开始用中文提问

### 🎯 推荐的首次查询

试试这些查询来验证所有功能正常：

#### 基础验证查询
```
"显示逾期率分析数据库中的所有表"
"查看客户信息表有多少条记录"
"连接到overdue_analysis数据库"
```

#### 逾期率分析查询（已完全修复）
```
"帮我分析逾期率"
"帮我分析5月份的逾期数据，并找出逾期的根因，不止返回sql还需要有报告"
"计算30天以上的逾期率，并生成分析报告"
"按省份分析逾期风险"
```

#### 高级分析查询
```
"不同信用评分客户的逾期表现如何？"
"利率对逾期率有什么影响？"
"哪个贷款金额区间的逾期率最高？"
"分析不同职业的逾期风险"
```

## 🌟 项目功能亮点

### 智能错误处理 ✅
- 不再显示通用的"Generate view content failed"错误
- 显示具体的SQL错误信息和修复建议
- 用户友好的中文错误解释

### SQL自动修复 ✅
- 自动修复AI生成的常见SQL问题
- CTE别名不匹配自动修复
- 中文字段名自动处理

### 详细分析报告 ✅
当您要求分析时，系统会生成包含以下内容的完整报告：
- 📝 **分析摘要**: 简要总结分析结果
- 🔍 **关键发现**: 从数据中发现的关键事实和趋势
- 💡 **业务洞察**: 基于数据的业务解释和见解
- 🎯 **建议措施**: 基于分析结果的具体行动建议
- 🔬 **分析方法**: 分析方法和逻辑的说明

### 完整测试数据 ✅
- 96条逾期率统计数据，覆盖2023年4-7月
- 完整的客户信息和贷款数据
- 真实的业务场景数据

## 🛠️ 管理命令

### Ubuntu系统管理命令

#### 日常管理
```bash
# 查看容器状态
docker ps

# 查看详细状态
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 完全重启
docker-compose down && docker-compose up -d

# 查看服务状态
sudo systemctl status docker
```

#### 日志查看
```bash
# 查看webserver日志
docker logs db-gpt-webserver-1 --tail 20

# 查看数据库日志
docker logs db-gpt-db-1 --tail 20

# 实时查看日志
docker logs -f db-gpt-webserver-1

# 查看所有服务日志
docker-compose logs -f
```

#### 数据库管理
```bash
# 连接到数据库
docker exec -it db-gpt-db-1 mysql -u root -paa123456

# 查看特定数据库的表
docker exec db-gpt-db-1 mysql -u root -paa123456 overdue_analysis -e "SHOW TABLES;"

# 检查数据量
docker exec db-gpt-db-1 mysql -u root -paa123456 overdue_analysis -e "SELECT COUNT(*) FROM overdue_rate_stats;"

# 备份数据库
docker exec db-gpt-db-1 mysqldump -u root -paa123456 overdue_analysis > backup_$(date +%Y%m%d).sql
```

### Windows系统管理命令

#### 日常管理
```powershell
# 查看容器状态
docker ps

# 查看详细状态
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 完全重启
docker-compose down; docker-compose up -d
```

#### 日志查看
```powershell
# 查看webserver日志
docker logs db-gpt-webserver-1 --tail 20

# 查看数据库日志
docker logs db-gpt-db-1 --tail 20

# 实时查看日志
docker logs -f db-gpt-webserver-1
```

#### 数据库管理
```powershell
# 连接到数据库
docker exec -it db-gpt-db-1 mysql -u root -paa123456

# 查看特定数据库的表
docker exec db-gpt-db-1 mysql -u root -paa123456 overdue_analysis -e "SHOW TABLES;"

# 检查数据量
docker exec db-gpt-db-1 mysql -u root -paa123456 overdue_analysis -e "SELECT COUNT(*) FROM overdue_rate_stats;"
```

## 📋 数据库信息

### 系统数据库 (dbgpt)
- **用途**: DB-GPT系统表和配置
- **端口**: 3307
- **访问**: 系统内部使用

### 逾期率分析数据库 (overdue_analysis)
- **用途**: 业务数据分析
- **数据量**: 96条逾期率统计记录
- **时间范围**: 2023年4-7月
- **表结构**:
  - `customer_info` - 客户基本信息
  - `loan_info` - 贷款基本信息  
  - `lending_details` - 还款明细记录
  - `overdue_rate_stats` - 逾期率统计表（主要分析表）
  - `risk_factor_analysis` - 风险因子分析表

## 🔧 故障排除

### Ubuntu系统故障排除

#### Docker服务问题
**症状**: `Cannot connect to the Docker daemon`

**解决方案**:
```bash
# 启动Docker服务
sudo systemctl start docker

# 检查Docker服务状态
sudo systemctl status docker

# 如果用户权限问题
sudo usermod -aG docker $USER
newgrp docker

# 重启Docker服务
sudo systemctl restart docker
```

#### 容器启动失败
**症状**: 容器状态显示"Exited"

**解决方案**:
```bash
# 查看错误日志
docker logs db-gpt-webserver-1
docker logs db-gpt-db-1

# 检查端口占用
sudo netstat -tlnp | grep :5670
sudo netstat -tlnp | grep :3307

# 重启容器
docker-compose restart

# 如果仍有问题，完全重启
docker-compose down
docker-compose up -d
```

#### 权限问题
**症状**: `Permission denied`

**解决方案**:
```bash
# 检查文件权限
ls -la docker-compose.yml

# 修改文件权限
chmod 644 docker-compose.yml
chmod 755 configs/

# 检查Docker组权限
groups $USER

# 如果不在docker组中
sudo usermod -aG docker $USER
newgrp docker
```

### Windows系统故障排除

#### Docker Desktop未启动
**症状**: `error during connect: Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine..."`

**解决方案**:
```powershell
# 启动Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 等待启动完成（1-2分钟）
Start-Sleep -Seconds 60

# 验证启动
docker version
```

#### 容器启动失败
**症状**: 容器状态显示"Exited"

**解决方案**:
```powershell
# 查看错误日志
docker logs db-gpt-webserver-1
docker logs db-gpt-db-1

# 重启容器
docker-compose restart

# 如果仍有问题，完全重启
docker-compose down
docker-compose up -d
```

### 通用问题解决

#### Web应用无法访问
**症状**: http://localhost:5670 无法打开

**解决方案**:
```bash
# Ubuntu
sudo netstat -tlnp | grep :5670
docker logs db-gpt-webserver-1 --tail 50
docker-compose restart webserver

# Windows
netstat -an | findstr :5670
docker logs db-gpt-webserver-1 --tail 50
docker-compose restart webserver
```

#### 数据库连接问题
**症状**: 查询时提示数据库连接失败

**解决方案**:
```bash
# 测试数据库连接
docker exec db-gpt-db-1 mysql -u root -paa123456 -e "SELECT 1;"

# 检查数据库状态
docker ps | grep mysql

# 重启数据库
docker-compose restart db

# 等待数据库完全启动
sleep 30
```

#### 查询返回空结果
**可能原因**: 数据库中没有数据

**解决方案**:
```bash
# 检查数据是否存在
docker exec db-gpt-db-1 mysql -u root -paa123456 overdue_analysis -e "SELECT COUNT(*) FROM overdue_rate_stats;"

# 如果没有数据，重新初始化
docker-compose down
docker-compose up -d
```

## 📞 获取帮助

### 日志收集

#### Ubuntu系统
```bash
# 收集系统信息
echo "=== 系统信息 ===" > debug_info.txt
uname -a >> debug_info.txt
docker --version >> debug_info.txt
docker-compose --version >> debug_info.txt

echo "=== 容器状态 ===" >> debug_info.txt
docker ps -a >> debug_info.txt

echo "=== 应用日志 ===" >> debug_info.txt
docker logs db-gpt-webserver-1 --tail 100 >> debug_info.txt

echo "=== 数据库日志 ===" >> debug_info.txt
docker logs db-gpt-db-1 --tail 100 >> debug_info.txt
```

#### Windows系统
```powershell
# 收集系统信息
"=== 系统信息 ===" | Out-File debug_info.txt
Get-ComputerInfo | Out-File debug_info.txt -Append
docker --version | Out-File debug_info.txt -Append

"=== 容器状态 ===" | Out-File debug_info.txt -Append
docker ps -a | Out-File debug_info.txt -Append

"=== 应用日志 ===" | Out-File debug_info.txt -Append
docker logs db-gpt-webserver-1 --tail 100 | Out-File debug_info.txt -Append
```

### 重置项目

#### 完全重置（Ubuntu/Windows通用）
```bash
# 停止并删除所有容器
docker-compose down -v

# 清理Docker缓存（可选）
docker system prune -f

# 清理未使用的镜像（可选）
docker image prune -f

# 重新启动
docker-compose up -d
```

### 性能优化

#### Ubuntu系统优化
```bash
# 检查系统资源
free -h
df -h
docker stats

# 优化Docker配置
sudo nano /etc/docker/daemon.json
# 添加以下内容：
# {
#   "log-driver": "json-file",
#   "log-opts": {
#     "max-size": "10m",
#     "max-file": "3"
#   }
# }

# 重启Docker服务
sudo systemctl restart docker
```

## 🚀 生产环境部署建议

### Ubuntu生产环境
```bash
# 1. 使用环境变量文件
cp .env.example .env
nano .env

# 2. 配置反向代理（Nginx示例）
sudo apt install nginx -y

# 3. 配置SSL证书（Let's Encrypt）
sudo apt install certbot python3-certbot-nginx -y

# 4. 设置防火墙
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# 5. 配置日志轮转
sudo nano /etc/logrotate.d/dbgpt
```

### 监控和维护
```bash
# 设置定时任务检查服务状态
crontab -e
# 添加：*/5 * * * * /path/to/health_check.sh

# 创建健康检查脚本
cat > health_check.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:5670 > /dev/null 2>&1; then
    echo "$(date): DB-GPT服务异常，正在重启..." >> /var/log/dbgpt_health.log
    cd /path/to/DB-GPT && docker-compose restart
fi
EOF

chmod +x health_check.sh
```

---

## 🎉 开始您的数据分析之旅

现在您可以：

1. ✅ **访问应用**: http://localhost:5670
2. ✅ **智能对话**: 用中文直接提问
3. ✅ **逾期率分析**: 获得详细的分析报告
4. ✅ **风险评估**: 多维度数据洞察
5. ✅ **业务决策**: 基于数据的建议措施

### 🚀 立即开始
在聊天界面中输入您的第一个问题：
```
"帮我分析逾期率，并生成详细报告"
```

### 📚 更多资源
- **项目文档**: 查看项目根目录下的其他文档
- **配置文件**: `configs/dbgpt-overdue-analysis.toml`
- **Docker配置**: `docker-compose.yml`

祝您使用愉快！🎉 