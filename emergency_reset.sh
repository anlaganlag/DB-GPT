#!/bin/bash

echo "⚠️  紧急回滚脚本 ⚠️"
echo "当前暂存区文件数量: $(git status --porcelain | grep '^[AMDRC]' | wc -l)"

echo -e "\n选择操作:"
echo "1. 撤销所有暂存区文件 (git reset HEAD)"
echo "2. 撤销所有更改并恢复到最后一次提交 (git reset --hard HEAD)"
echo "3. 只查看暂存区文件列表"
echo "4. 退出"

read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "正在撤销所有暂存区文件..."
        git reset HEAD
        echo "✅ 已撤销所有暂存区文件，文件仍在工作区"
        ;;
    2)
        echo "⚠️  警告：这将丢失所有未提交的更改！"
        read -p "确认要继续吗? (yes/no): " confirm
        if [[ $confirm == "yes" ]]; then
            git reset --hard HEAD
            echo "✅ 已恢复到最后一次提交状态"
        else
            echo "❌ 操作已取消"
        fi
        ;;
    3)
        echo -e "\n📋 暂存区文件列表:"
        git status --porcelain | grep '^[AMDRC]' | nl
        ;;
    4)
        echo "退出脚本"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo -e "\n当前状态:"
echo "暂存区文件数量: $(git status --porcelain | grep '^[AMDRC]' | wc -l)"
echo "工作区文件数量: $(git status --porcelain | grep '^[^AMDRC]' | wc -l)" 