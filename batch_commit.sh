#!/bin/bash

echo "=== Git 分批提交脚本 ==="
echo "当前暂存区文件数量: $(git status --porcelain | grep '^[AMDRC]' | wc -l)"

# 1. 提交配置文件
echo -e "\n📁 第1批：提交配置文件..."
git status --porcelain | grep '^[AMDRC]' | grep -E '\.(yml|yaml|toml|json)$' | cut -c4- | while read file; do
    echo "  - $file"
done

read -p "是否提交配置文件? (y/n): " confirm
if [[ $confirm == [yY] ]]; then
    git status --porcelain | grep '^[AMDRC]' | grep -E '\.(yml|yaml|toml|json)$' | cut -c4- | xargs -I {} git add "{}"
    git commit -m "配置文件更新: 更新Docker配置和数据源配置"
    echo "✅ 配置文件提交完成"
fi

# 2. 提交Python脚本
echo -e "\n🐍 第2批：提交Python脚本..."
git status --porcelain | grep '^[AMDRC]' | grep -E '\.py$' | cut -c4- | while read file; do
    echo "  - $file"
done

read -p "是否提交Python脚本? (y/n): " confirm
if [[ $confirm == [yY] ]]; then
    git status --porcelain | grep '^[AMDRC]' | grep -E '\.py$' | cut -c4- | xargs -I {} git add "{}"
    git commit -m "Python脚本更新: 添加数据库连接和修复脚本"
    echo "✅ Python脚本提交完成"
fi

# 3. 提交Shell脚本和SQL文件
echo -e "\n🔧 第3批：提交脚本和SQL文件..."
git status --porcelain | grep '^[AMDRC]' | grep -E '\.(sh|sql)$' | cut -c4- | while read file; do
    echo "  - $file"
done

read -p "是否提交脚本和SQL文件? (y/n): " confirm
if [[ $confirm == [yY] ]]; then
    git status --porcelain | grep '^[AMDRC]' | grep -E '\.(sh|sql)$' | cut -c4- | xargs -I {} git add "{}"
    git commit -m "脚本和SQL文件: 添加数据库初始化和修复脚本"
    echo "✅ 脚本和SQL文件提交完成"
fi

# 4. 提交文档文件
echo -e "\n📚 第4批：提交文档文件..."
git status --porcelain | grep '^[AMDRC]' | grep -E '\.(md|pdf)$' | cut -c4- | while read file; do
    echo "  - $file"
done

read -p "是否提交文档文件? (y/n): " confirm
if [[ $confirm == [yY] ]]; then
    git status --porcelain | grep '^[AMDRC]' | grep -E '\.(md|pdf)$' | cut -c4- | xargs -I {} git add "{}"
    git commit -m "文档更新: 添加项目文档和技术方案"
    echo "✅ 文档文件提交完成"
fi

# 5. 提交其他文件
echo -e "\n📄 第5批：提交其他文件..."
git status --porcelain | grep '^[AMDRC]' | grep -v -E '\.(py|sh|sql|yml|yaml|toml|json|md|pdf)$' | cut -c4- | while read file; do
    echo "  - $file"
done

read -p "是否提交其他文件? (y/n): " confirm
if [[ $confirm == [yY] ]]; then
    git status --porcelain | grep '^[AMDRC]' | grep -v -E '\.(py|sh|sql|yml|yaml|toml|json|md|pdf)$' | cut -c4- | xargs -I {} git add "{}"
    git commit -m "其他文件更新: 添加其他项目文件"
    echo "✅ 其他文件提交完成"
fi

echo -e "\n🎉 分批提交完成！"
echo "剩余暂存区文件数量: $(git status --porcelain | grep '^[AMDRC]' | wc -l)" 