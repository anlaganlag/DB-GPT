# 🚀 DB-GPT Project Setup & Running Guide

This guide will help you set up and run the DB-GPT project on your Windows system. There are multiple ways to run the project - choose the one that best fits your environment.

## 📋 Prerequisites

- **Python 3.10+** (Required)
- **Git** (Already installed since you cloned the repo)
- **Docker & Docker Compose** (Optional, for containerized setup)
- **MySQL** (Optional, can use Docker)

## 🎯 Quick Start Options

### Option 1: 🐳 Docker Compose (Recommended for Beginners)

This is the easiest way to get started with minimal configuration.

#### Step 1: Set up Environment Variables
```bash
# Create a .env file in the project root
echo "SILICONFLOW_API_KEY=your_api_key_here" > .env
```

#### Step 2: Run with Docker Compose
```bash
# Start all services (MySQL + DB-GPT)
docker compose up -d

# Check if services are running
docker compose ps

# View logs
docker compose logs -f webserver
```

#### Step 3: Access the Application
- **Web Interface**: http://localhost:5670
- **MySQL**: localhost:3306 (user: root, password: aa123456)

#### Step 4: Stop Services
```bash
docker compose down
```

### Option 2: 🛠️ Local Development Setup (Recommended for Development)

This gives you full control and allows you to modify the code.

#### Step 1: Install UV (Modern Python Package Manager)
```bash
# Install UV (faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh
# or on Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Step 2: Use the Installation Helper
```bash
# Interactive installation guide
python install_help.py install-cmd --interactive

# Or list available options
python install_help.py list --verbose
```

#### Step 3: Install Dependencies
```bash
# Install all dependencies
uv sync

# Or install specific features (example)
uv pip install -e "packages/dbgpt-core[openai,mysql]"
uv pip install -e "packages/dbgpt-app"
uv pip install -e "packages/dbgpt-serve"
```

#### Step 4: Set up Database
```bash
# Option A: Use Docker for MySQL
docker run -d \
  --name dbgpt-mysql \
  -e MYSQL_ROOT_PASSWORD=aa123456 \
  -e MYSQL_DATABASE=dbgpt \
  -p 3306:3306 \
  mysql:8.0

# Option B: Use existing MySQL and run our schema fix
mysql -u root -p < fix_database_schema.sql
```

#### Step 5: Configure DB-GPT
```bash
# Copy example config
cp configs/config.toml.template configs/config.toml

# Edit the config file with your settings
# - Database connection
# - API keys (OpenAI, etc.)
# - Model paths
```

#### Step 6: Initialize Database
```bash
# Run database migrations
uv run dbgpt db init

# Or if using the workspace
cd packages/dbgpt-core
uv run python -m dbgpt.cli.cli db init
```

#### Step 7: Start the Application
```bash
# Start the web server
uv run dbgpt start webserver

# Or with specific config
uv run dbgpt start webserver --config configs/config.toml
```

### Option 3: 🎯 Quick Test with Preset Configurations

Use the built-in deployment presets for common scenarios.

#### List Available Presets
```bash
python install_help.py deploy --list
```

#### Deploy with OpenAI Preset
```bash
python install_help.py deploy --preset openai
# Follow the generated commands
```

#### Deploy with Local Model Preset
```bash
python install_help.py deploy --preset glm4
# Follow the generated commands
```

## 🔧 Configuration

### Database Configuration
Edit `configs/config.toml`:
```toml
[DB]
db_type = "mysql"
db_host = "localhost"
db_port = 3306
db_user = "root"
db_password = "aa123456"
db_name = "dbgpt"
```

### LLM Configuration
```toml
[LLM]
llm_model = "openai_proxyllm"
model_name = "gpt-3.5-turbo"
api_key = "your_openai_api_key"
api_base = "https://api.openai.com/v1"
```

## 🐛 Troubleshooting

### Common Issues

1. **SQL Column Errors** (Already Fixed!)
   - We've implemented SQL validation
   - Enhanced prompts for better column detection
   - Added database schema inspection tools

2. **Port Already in Use**
   ```bash
   # Check what's using port 5670
   netstat -ano | findstr :5670
   # Kill the process or change port in config
   ```

3. **Database Connection Issues**
   ```bash
   # Test database connection
   python inspect_database_schema.py
   ```

4. **Missing Dependencies**
   ```bash
   # Reinstall all dependencies
   uv sync --reinstall
   ```

### Useful Commands

```bash
# Check project status
python install_help.py list

# Inspect database schema
python inspect_database_schema.py

# Run tests
uv run pytest

# Check logs
tail -f logs/dbgpt.log
```

## 🌐 Accessing the Application

Once running, you can access:

- **Main Web Interface**: http://localhost:5670
- **API Documentation**: http://localhost:5670/docs
- **Chat Interface**: http://localhost:5670/chat
- **Database Management**: http://localhost:5670/database

## 📚 Next Steps

1. **Explore the Web Interface**: Try different chat modes
2. **Connect Your Database**: Add your own data sources
3. **Customize Agents**: Create custom AI agents
4. **Build AWEL Flows**: Create workflow automations
5. **Fine-tune Models**: Train models on your data

## 🆘 Getting Help

- **Documentation**: http://docs.dbgpt.cn/
- **GitHub Issues**: https://github.com/eosphoros-ai/DB-GPT/issues
- **Discord**: https://discord.gg/7uQnPuveTY

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Web interface loads at http://localhost:5670
- ✅ Database connection is successful
- ✅ Chat responses are generated without SQL errors
- ✅ No error messages in the logs

Happy coding with DB-GPT! 🚀 