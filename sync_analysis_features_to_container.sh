#!/bin/bash

echo "🚀 同步分析报告功能到容器"
echo "================================"

# 1. 复制数据驱动分析器到容器
echo "📁 复制数据驱动分析器..."
docker cp ./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/data_driven_analyzer.py \
    db-gpt_webserver_1:/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/

# 2. 复制增强的输出解析器到容器
echo "📁 复制增强的输出解析器..."
docker cp ./packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/out_parser.py \
    db-gpt_webserver_1:/app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/

# 3. 验证文件是否成功复制
echo "✅ 验证文件复制..."
docker exec db-gpt_webserver_1 ls -la /app/packages/dbgpt-app/src/dbgpt_app/scene/chat_db/auto_execute/ | grep -E "(data_driven_analyzer|out_parser)"

# 4. 测试分析器导入
echo "🧪 测试分析器导入..."
docker exec db-gpt_webserver_1 python3 -c "
try:
    from dbgpt_app.scene.chat_db.auto_execute.data_driven_analyzer import DataDrivenAnalyzer
    print('✅ DataDrivenAnalyzer 导入成功')
    
    analyzer = DataDrivenAnalyzer()
    print('✅ DataDrivenAnalyzer 初始化成功')
    
    # 测试关键词检测
    test_input = '根据sql结果分析逾期率生成根因报告'
    result = analyzer.should_generate_analysis_report(test_input)
    print(f'✅ 关键词检测结果: {result}')
    
except Exception as e:
    print(f'❌ 测试失败: {e}')
    import traceback
    traceback.print_exc()
"

# 5. 重启容器以确保更改生效
echo "🔄 重启容器以应用更改..."
read -p "是否重启容器? (y/n): " restart_choice
if [[ $restart_choice == [yY] ]]; then
    echo "正在重启容器..."
    docker restart db-gpt_webserver_1
    
    echo "等待容器启动..."
    sleep 10
    
    echo "✅ 容器重启完成"
else
    echo "⚠️ 建议重启容器以确保更改完全生效"
fi

echo ""
echo "🎉 同步完成！"
echo "现在您可以测试分析报告功能："
echo "1. 在DB-GPT界面中输入包含'分析'、'报告'等关键词的查询"
echo "2. 系统将自动生成基于真实数据的分析报告" 