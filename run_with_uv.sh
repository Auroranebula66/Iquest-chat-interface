#!/bin/bash

# 设置脚本变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/.venv"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
PYTHON_SCRIPT="$PROJECT_DIR/app.py"

# 函数：打印消息
print_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 检查uv是否已安装
if ! command -v uv &> /dev/null; then
    print_message "错误: uv 未安装。请先安装uv。"
    exit 1
fi

# 检查requirements.txt是否存在
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    print_message "错误: $REQUIREMENTS_FILE 文件不存在。"
    exit 1
fi

print_message "开始创建虚拟环境并安装依赖..."

# 使用uv创建虚拟环境并安装依赖
print_message "创建虚拟环境: $VENV_DIR"
uv venv "$VENV_DIR"

if [ $? -ne 0 ]; then
    print_message "错误: 创建虚拟环境失败。"
    exit 1
fi

print_message "激活虚拟环境并安装依赖..."
source "$VENV_DIR/bin/activate"

# 使用uv sync安装requirements.txt中的所有包
uv pip install -r "$REQUIREMENTS_FILE"

if [ $? -ne 0 ]; then
    print_message "错误: 安装依赖失败。"
    exit 1
fi

print_message "依赖安装完成。"

# 运行Python脚本
print_message "启动应用..."
cd "$PROJECT_DIR"
python "$PYTHON_SCRIPT"

# 捕获退出信号并优雅地关闭
trap 'print_message "正在关闭应用..."; exit' INT TERM

print_message "应用已结束。"