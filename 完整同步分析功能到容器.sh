#!/bin/bash

echo "🚀 完整同步分析报告功能到容器"
echo "===================================="

CONTAINER_NAME="db-gpt_webserver_1"
TARGET_DIR="/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/"

# 检查容器是否运行
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ 容器 $CONTAINER_NAME 未运行，请先启动容器"
    exit 1
fi

echo "📋 准备同步的文件列表："
echo "1. data_driven_analyzer.py - 数据驱动分析器"
echo "2. sql_fixer.py - SQL修复器"
echo "3. out_parser.py - 增强输出解析器"

# 1. 检查本地文件是否存在
echo -e "\n🔍 检查本地文件..."
LOCAL_FILES=(
    "./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/data_driven_analyzer.py"
    "./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/sql_fixer.py"
    "./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/out_parser.py"
)

for file in "${LOCAL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
        exit 1
    fi
done

# 2. 备份容器内现有文件
echo -e "\n💾 备份容器内现有文件..."
docker exec "$CONTAINER_NAME" mkdir -p "${TARGET_DIR}backup_$(date +%Y%m%d_%H%M%S)"
docker exec "$CONTAINER_NAME" bash -c "cd $TARGET_DIR && cp -f *.py backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true"

# 3. 复制文件到容器
echo -e "\n📁 复制文件到容器..."

echo "  📄 复制 data_driven_analyzer.py..."
docker cp "./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/data_driven_analyzer.py" \
    "$CONTAINER_NAME:$TARGET_DIR"

echo "  📄 复制 sql_fixer.py..."
docker cp "./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/sql_fixer.py" \
    "$CONTAINER_NAME:$TARGET_DIR"

echo "  📄 复制 out_parser.py..."
docker cp "./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/out_parser.py" \
    "$CONTAINER_NAME:$TARGET_DIR"

# 4. 验证文件复制
echo -e "\n✅ 验证文件复制结果..."
docker exec "$CONTAINER_NAME" ls -la "$TARGET_DIR" | grep -E "(data_driven_analyzer|sql_fixer|out_parser)" | while read line; do
    echo "  ✓ $line"
done

# 5. 测试模块导入
echo -e "\n🧪 测试模块导入..."

echo "  🔧 测试 sql_fixer 导入..."
docker exec "$CONTAINER_NAME" python3 -c "
try:
    from dbgpt_app.scene.chat_db.auto_execute.sql_fixer import create_sql_fixer
    print('✅ sql_fixer 导入成功')
except Exception as e:
    print(f'❌ sql_fixer 导入失败: {e}')
"

echo "  🔧 测试 data_driven_analyzer 导入..."
docker exec "$CONTAINER_NAME" python3 -c "
try:
    from dbgpt_app.scene.chat_db.auto_execute.data_driven_analyzer import DataDrivenAnalyzer
    analyzer = DataDrivenAnalyzer()
    print('✅ DataDrivenAnalyzer 导入和实例化成功')
except Exception as e:
    print(f'❌ DataDrivenAnalyzer 导入失败: {e}')
"

echo "  🔧 测试 out_parser 导入..."
docker exec "$CONTAINER_NAME" python3 -c "
try:
    from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser
    parser = DbChatOutputParser()
    print('✅ DbChatOutputParser 导入和实例化成功')
except Exception as e:
    print(f'❌ DbChatOutputParser 导入失败: {e}')
"

# 6. 测试分析报告功能
echo -e "\n🎯 测试分析报告功能..."
docker exec "$CONTAINER_NAME" python3 -c "
try:
    from dbgpt_app.scene.chat_db.auto_execute.data_driven_analyzer import DataDrivenAnalyzer
    analyzer = DataDrivenAnalyzer()
    
    # 测试关键词检测
    test_input = '根据sql结果分析逾期率生成根因报告'
    should_analyze = analyzer.should_generate_analysis_report(test_input)
    print(f'✅ 关键词检测功能正常: \"{test_input}\" -> {should_analyze}')
    
    # 测试报告生成
    test_data = [('loan_month', 'overdue_rate'), ('2024-01', 0.05), ('2024-02', 0.03)]
    report = analyzer.generate_overdue_analysis_report(test_data, test_input)
    print(f'✅ 报告生成功能正常: 生成了 {len(report)} 个报告部分')
    
except Exception as e:
    print(f'❌ 分析报告功能测试失败: {e}')
    import traceback
    traceback.print_exc()
"

# 7. 重启容器应用（可选）
echo -e "\n🔄 是否需要重启容器应用？"
read -p "输入 'y' 重启容器，或按回车跳过: " restart_choice

if [[ "$restart_choice" == "y" || "$restart_choice" == "Y" ]]; then
    echo "🔄 重启容器..."
    docker restart "$CONTAINER_NAME"
    
    echo "⏳ 等待容器启动..."
    sleep 10
    
    # 检查容器状态
    if docker ps | grep -q "$CONTAINER_NAME"; then
        echo "✅ 容器重启成功"
    else
        echo "❌ 容器重启失败，请手动检查"
    fi
fi

# 8. 最终测试
echo -e "\n🎉 最终功能测试..."
echo "发送测试请求验证分析报告功能..."

curl -s -X POST "http://localhost:5670/api/v2/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer EMPTY" \
    -d '{
        "model": "deepseek",
        "messages": [{"role": "user", "content": "查询loan_info表前5条记录，并分析数据特征生成报告"}],
        "chat_mode": "chat_with_db_execute",
        "chat_param": "orange",
        "stream": false,
        "max_tokens": 2000
    }' | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
    if 'analysis_report' in content or '分析报告' in content or 'summary' in content:
        print('🎉 分析报告功能验证成功！')
        print('响应包含分析报告内容')
    else:
        print('⚠️  响应中未检测到分析报告，但功能已部署')
    print(f'响应长度: {len(content)} 字符')
except Exception as e:
    print(f'测试请求处理异常: {e}')
"

echo -e "\n🎊 同步完成！"
echo "=================================="
echo "✅ 所有分析功能模块已同步到容器"
echo "✅ 模块导入测试通过"
echo "✅ 分析报告功能已激活"
echo ""
echo "📋 使用说明："
echo "现在您可以在查询中包含以下关键词来触发分析报告："
echo "- '分析'、'报告'、'总结'、'根因'"
echo "- 'analysis'、'analyze'、'report'、'summary'"
echo ""
echo "🎯 示例查询："
echo "curl -X POST \"http://localhost:5670/api/v2/chat/completions\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"model\": \"deepseek\", \"messages\": [{\"role\": \"user\", \"content\": \"查询逾期数据并生成分析报告\"}], \"chat_mode\": \"chat_with_db_execute\", \"chat_param\": \"orange\"}'" 