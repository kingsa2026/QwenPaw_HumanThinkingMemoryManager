#!/bin/bash

# Human Thinking Memory Manager 一键安装脚本
# 从 GitHub 拉取仓库并自动安装

echo "=== Human Thinking Memory Manager 一键安装脚本 ==="
echo "从 GitHub 拉取仓库并自动安装 Human Thinking Memory Manager"

# 检查是否安装了 git
if ! command -v git &> /dev/null; then
    echo "错误: 未安装 git，请先安装 git 后再运行此脚本"
    exit 1
fi

# 检查是否在 QwenPaw 目录中
if [ ! -d "src/qwenpaw" ]; then
    echo "错误: 请在 QwenPaw 根目录运行此脚本"
    exit 1
fi

# 定义变量
QwenPaw_PATH=$(pwd)
TOOLS_DIR="$QwenPaw_PATH/src/qwenpaw/agents/tools"
HUMAN_THINKING_DIR="$TOOLS_DIR/HumanThinkingMemoryManager"
GITHUB_REPO="https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager.git"

# 检查 HumanThinkingMemoryManager 目录是否已存在
if [ -d "$HUMAN_THINKING_DIR" ]; then
    echo "警告: HumanThinkingMemoryManager 目录已存在，将更新到最新版本"
    cd "$HUMAN_THINKING_DIR"
    git pull
    cd "$QwenPaw_PATH"
else
    echo "克隆 GitHub 仓库..."
    git clone "$GITHUB_REPO" "$HUMAN_THINKING_DIR"
fi

# 运行安装脚本
echo "运行安装脚本..."
cd "$HUMAN_THINKING_DIR"
chmod +x install.sh
./install.sh

# 返回到 QwenPaw 根目录
cd "$QwenPaw_PATH"

echo "\n=== 安装完成 ==="
echo "Human Thinking Memory Manager 已成功安装"
echo "请在 config.py 中设置 memory_manager.backend = \"human_thinking\" 以启用"
echo "然后重启 QwenPaw 服务以应用更改"
