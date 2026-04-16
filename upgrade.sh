#!/bin/bash
# 一键升级脚本 - 从旧版本升级到 1.0.2-beta0.1

set -e

echo "=================================="
echo "Human Thinking Memory Manager 升级脚本"
echo "目标版本: 1.0.2-beta0.1"
echo "=================================="

# 检测当前目录
if [ ! -d "core" ] && [ ! -d "HumanThinkingMemoryManager" ]; then
    echo "错误: 请在 QwenPaw_HumanThinkingMemoryManager 目录中运行此脚本"
    exit 1
fi

# 检测QwenPaw路径
QWENPAW_PATH=""
if [ -d "../../../src/qwenpaw" ]; then
    QWENPAW_PATH="../../../"
elif [ -d "../../src/qwenpaw" ]; then
    QWENPAW_PATH="../../"
elif [ -d "../src/qwenpaw" ]; then
    QWENPAW_PATH="../"
else
    echo "警告: 未找到 QwenPaw 安装目录"
    echo "请确保此脚本在 QwenPaw/tools/HumanThinkingMemoryManager 目录中运行"
fi

# 备份旧版本
echo "\n1. 备份旧版本..."
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz"

if [ -d "HumanThinkingMemoryManager" ]; then
    tar -czf "$BACKUP_FILE" HumanThinkingMemoryManager
    echo "已备份旧版本到: $BACKUP_FILE"
else
    echo "未找到旧版本目录，跳过备份"
fi

# 清理旧文件
echo "\n2. 清理旧文件..."
if [ -d "HumanThinkingMemoryManager" ]; then
    rm -rf HumanThinkingMemoryManager
    echo "已删除旧版本目录"
fi

# 下载新版本
echo "\n3. 下载新版本..."
GITHUB_REPO="kingsa2026/QwenPaw_HumanThinkingMemoryManager"
RELEASE_TAG="v1.0.2-beta0.1"

# 下载最新版本的代码
if command -v git &> /dev/null; then
    echo "使用 git 克隆最新版本..."
    git pull origin main
else
    echo "未安装 git，跳过代码更新"
fi

# 安装到 QwenPaw
echo "\n4. 安装到 QwenPaw..."
if [ -n "$QWENPAW_PATH" ]; then
    # 复制文件到 QwenPaw 的 tools 目录
    TOOLS_DIR="$QWENPAW_PATH/src/qwenpaw/agents/tools"
    mkdir -p "$TOOLS_DIR"
    
    # 复制核心文件
    cp -r core "$TOOLS_DIR/"
    cp -r search "$TOOLS_DIR/"
    cp -r hooks "$TOOLS_DIR/"
    cp -r utils "$TOOLS_DIR/"
    cp -r config "$TOOLS_DIR/"
    cp install.sh "$TOOLS_DIR/"
    cp uninstall.sh "$TOOLS_DIR/"
    
    echo "已安装到 QwenPaw tools 目录"
else
    echo "未找到 QwenPaw 目录，跳过安装"
fi

# 运行数据库升级
echo "\n5. 运行数据库升级..."
if [ -f "core/database.py" ]; then
    echo "数据库结构已更新，下次启动时会自动升级"
else
    echo "未找到数据库文件，跳过升级"
fi

echo "\n=================================="
echo "升级完成！"
echo "目标版本: 1.0.2-beta0.1"
echo "\n新功能："
echo "- 智能记忆管理：记忆分类、记忆关联、记忆摘要、记忆优先级"
echo "- 数据库结构优化"
echo "- 版本管理改进"
echo "\n请重启 QwenPaw 以应用更改"
echo "=================================="
