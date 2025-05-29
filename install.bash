#!/bin/bash

# 设置UTF-8编码
export LANG=en_US.UTF-8

# 步骤1：获取当前脚本所在目录（即项目根目录）
project_path=$(dirname "$(readlink -f "$0")")

# 步骤2：将项目路径添加到用户环境变量PATH
if ! grep -q "export PATH=\$PATH:$project_path" ~/.bashrc; then
    echo "export PATH=\$PATH:$project_path" >> ~/.bashrc
    echo "[√] 已将项目路径添加到环境变量: $project_path"
else
    echo "[!] 环境变量已包含项目路径，无需重复添加"
fi

# 步骤3：配置bash的别名
# 检查用户是否有.bashrc文件，若没有则创建
if [ ! -f ~/.bashrc ]; then
    touch ~/.bashrc
    echo "[√] 已创建bash配置文件: ~/.bashrc"
fi

# 定义别名函数并写入配置文件
alias_code="
# G++ 错误翻译器别名
function gpro() {
    python3 \"$project_path/cpp_translator.py\" g++ \"\$@\"
}
"

# 检查是否已存在别名配置，避免重复添加
if ! grep -q "function gpro()" ~/.bashrc; then
    echo "$alias_code" >> ~/.bashrc
    echo "[√] 已添加g++别名到bash配置文件"
else
    echo "[!] 别名配置已存在，无需重复添加"
fi

# 步骤4：提示用户生效方式
echo -e "\n[完成] 请重启终端或执行以下命令立即生效:"
echo "  source ~/.bashrc"

# 设置脚本执行权限
chmod +x "$project_path/cpp_translator.py"
echo "[√] 已设置cpp_translator.py的执行权限"