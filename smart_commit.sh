#!/bin/bash

echo "🤖 智能Git提交助手"
echo "当前状态分析:"
echo "- 暂存区文件: $(git status --porcelain | grep '^[AMDRC]' | wc -l)"
echo "- 工作区文件: $(git status --porcelain | grep '^[^AMDRC]' | wc -l)"

# 分析文件类型
echo -e "\n📊 文件类型分析:"
echo "- Python文件: $(git status --porcelain | grep '^[AMDRC]' | grep '\.py$' | wc -l)"
echo "- Shell脚本: $(git status --porcelain | grep '^[AMDRC]' | grep '\.sh$' | wc -l)"
echo "- SQL文件: $(git status --porcelain | grep '^[AMDRC]' | grep '\.sql$' | wc -l)"
echo "- 配置文件: $(git status --porcelain | grep '^[AMDRC]' | grep -E '\.(yml|yaml|toml|json)$' | wc -l)"
echo "- 文档文件: $(git status --porcelain | grep '^[AMDRC]' | grep -E '\.(md|pdf)$' | wc -l)"

echo -e "\n🎯 提交策略选择:"
echo "1. 🔥 核心功能优先 (Python + SQL + 配置)"
echo "2. 📚 按类型分批提交"
echo "3. 🎲 交互式选择文件"
echo "4. 🚨 全部提交 (不推荐)"
echo "5. 📋 查看详细文件列表"
echo "6. 🔄 重置所有暂存区"

read -p "请选择策略 (1-6): " strategy

case $strategy in
    1)
        echo "🔥 执行核心功能优先提交..."
        
        # 核心功能文件
        core_files=$(git status --porcelain | grep '^[AMDRC]' | grep -E '\.(py|sql|yml|yaml|toml)$' | cut -c4-)
        if [[ -n "$core_files" ]]; then
            echo "核心功能文件:"
            echo "$core_files" | nl
            read -p "提交这些核心文件? (y/n): " confirm
            if [[ $confirm == [yY] ]]; then
                echo "$core_files" | xargs git add
                git commit -m "核心功能更新: Python脚本、SQL文件和配置文件"
                echo "✅ 核心功能文件提交完成"
            fi
        else
            echo "❌ 没有找到核心功能文件"
        fi
        ;;
        
    2)
        echo "📚 执行分批提交..."
        chmod +x batch_commit.sh
        ./batch_commit.sh
        ;;
        
    3)
        echo "🎲 交互式文件选择..."
        git status --porcelain | grep '^[AMDRC]' | cut -c4- | nl > /tmp/staged_files.txt
        
        echo "暂存区文件列表:"
        cat /tmp/staged_files.txt
        
        echo -e "\n输入要提交的文件编号 (用空格分隔，如: 1 3 5-8):"
        read -p "文件编号: " file_numbers
        
        if [[ -n "$file_numbers" ]]; then
            # 处理文件编号范围
            selected_files=""
            for num in $file_numbers; do
                if [[ $num == *-* ]]; then
                    # 处理范围 (如 5-8)
                    start=${num%-*}
                    end=${num#*-}
                    for ((i=start; i<=end; i++)); do
                        file=$(sed -n "${i}p" /tmp/staged_files.txt | cut -f2-)
                        selected_files="$selected_files $file"
                    done
                else
                    # 处理单个编号
                    file=$(sed -n "${num}p" /tmp/staged_files.txt | cut -f2-)
                    selected_files="$selected_files $file"
                fi
            done
            
            echo "选中的文件:"
            echo "$selected_files" | tr ' ' '\n' | grep -v '^$'
            
            read -p "输入提交信息: " commit_msg
            if [[ -n "$commit_msg" ]]; then
                echo "$selected_files" | xargs git add
                git commit -m "$commit_msg"
                echo "✅ 选中文件提交完成"
            fi
        fi
        
        rm -f /tmp/staged_files.txt
        ;;
        
    4)
        echo "🚨 警告：准备提交所有暂存区文件"
        git status --porcelain | grep '^[AMDRC]' | wc -l
        read -p "确认提交所有文件? (yes/no): " confirm
        if [[ $confirm == "yes" ]]; then
            read -p "输入提交信息: " commit_msg
            git commit -m "${commit_msg:-大批量文件更新}"
            echo "✅ 所有文件提交完成"
        fi
        ;;
        
    5)
        echo "📋 详细文件列表:"
        echo -e "\n🟢 新增文件 (A):"
        git status --porcelain | grep '^A' | cut -c4- | nl
        
        echo -e "\n🟡 修改文件 (M):"
        git status --porcelain | grep '^M' | cut -c4- | nl
        
        echo -e "\n🔴 删除文件 (D):"
        git status --porcelain | grep '^D' | cut -c4- | nl
        
        echo -e "\n🔄 重命名文件 (R):"
        git status --porcelain | grep '^R' | cut -c4-
        ;;
        
    6)
        echo "🔄 重置所有暂存区文件..."
        chmod +x emergency_reset.sh
        ./emergency_reset.sh
        ;;
        
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo -e "\n📊 操作后状态:"
echo "暂存区文件数量: $(git status --porcelain | grep '^[AMDRC]' | wc -l)" 