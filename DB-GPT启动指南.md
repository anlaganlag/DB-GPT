# DB-GPT 应用启动指南

## 🚀 应用已成功启动！

### ✅ 当前状态
- **Web应用地址**: http://localhost:5670
- **MySQL数据库端口**: 3307
- **系统状态**: 正常运行
- **逾期率分析数据库**: 已配置并可用

### 🔗 访问应用

1. **打开浏览器**，访问：
   ```
   http://localhost:5670
   ```

2. **开始使用**：
   - 进入聊天界面
   - 可以直接用中文提问
   - 支持自然语言转SQL查询

### 📊 连接逾期率分析数据库

#### 方法1：通过Web界面添加数据源

1. **进入数据库管理页面**
   - 在主界面找到"数据库"或"Database"选项
   - 点击"添加数据源"

2. **填写连接信息**：
   ```
   数据源名称: 逾期率分析数据库
   数据库类型: MySQL
   主机地址: localhost
   端口: 3307
   数据库名: overdue_analysis
   用户名: root
   密码: aa123456
   ```

3. **测试连接并保存**

#### 方法2：直接查询（推荐）

由于配置文件中已包含数据源配置，您可以直接在聊天界面中提问：

```
"连接到overdue_analysis数据库"
"显示逾期率分析数据库中的所有表"
"计算30天以上的逾期率"
```

### 🔍 示例查询

在聊天界面中，您可以直接使用以下中文提问：

#### 基础查询
- "显示所有客户信息"
- "查看贷款信息表的结构"
- "统计总共有多少笔贷款"

#### 逾期率分析
- "计算30天以上的逾期率"
- "按省份分析逾期风险"
- "不同信用评分客户的逾期表现如何？"
- "利率对逾期率有什么影响？"
- "哪个贷款金额区间的逾期率最高？"

#### 风险分析
- "分析不同职业的逾期风险"
- "按年龄段统计逾期情况"
- "显示高风险客户特征"
- "计算各个MOB的逾期率趋势"

### 🛠️ 管理命令

#### 启动应用
```bash
docker-compose up -d
```

#### 停止应用
```bash
docker-compose down
```

#### 重启应用
```bash
docker-compose restart
```

#### 查看日志
```bash
# 查看webserver日志
docker logs db-gpt-webserver-1

# 查看数据库日志
docker logs db-gpt-db-1
```

#### 检查状态
```bash
# 查看容器状态
docker ps

# 测试Web应用
curl http://localhost:5670
```

### 📋 数据库信息

#### 系统数据库 (dbgpt)
- **用途**: DB-GPT系统表和配置
- **端口**: 3307
- **访问**: 内部使用

#### 逾期率分析数据库 (overdue_analysis)
- **用途**: 业务数据分析
- **表结构**:
  - `customer_info` - 客户信息 (10条记录)
  - `loan_info` - 贷款信息 (10条记录)
  - `lending_details` - 还款明细 (包含逾期数据)
  - `overdue_rate_stats` - 逾期率统计表
  - `risk_factor_analysis` - 风险因子分析表

### 🔧 故障排除

#### 应用无法访问
1. 检查容器状态：`docker ps`
2. 查看日志：`docker logs db-gpt-webserver-1`
3. 重启服务：`docker-compose restart`

#### 数据库连接问题
1. 确认MySQL容器运行：`docker ps | grep mysql`
2. 测试数据库连接：
   ```bash
   docker exec db-gpt-db-1 mysql -u root -paa123456 -e "SHOW DATABASES;"
   ```

#### 查询无结果
1. 确认数据源已添加
2. 检查数据库中是否有数据：
   ```bash
   docker exec db-gpt-db-1 mysql -u root -paa123456 overdue_analysis -e "SELECT COUNT(*) FROM loan_info;"
   ```

### 📞 技术支持

如果遇到问题：
1. 查看详细日志：`docker logs db-gpt-webserver-1 --tail 50`
2. 检查配置文件：`configs/dbgpt-overdue-analysis.toml`
3. 重新启动：`docker-compose down && docker-compose up -d`

---

## 🎉 开始使用

现在您可以：
1. 访问 http://localhost:5670
2. 在聊天界面中直接提问
3. 进行逾期率分析和风险评估
4. 探索数据洞察和业务决策支持

祝您使用愉快！🚀 