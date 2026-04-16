#!/bin/bash
# Human Thinking Memory Manager 一键升级脚本
# 支持从任意旧版本升级到最新版本

set -e

echo "=================================="
echo "Human Thinking Memory Manager 升级脚本"
echo "目标版本: 1.0.2-beta0.3"
echo "=================================="

# 检测当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 查找Python
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "错误: 未找到Python解释器"
    exit 1
fi

# 检测QwenPaw路径
QWENPAW_PATH=""
if [ -d "$SCRIPT_DIR/../../../src/qwenpaw" ]; then
    QWENPAW_PATH="$SCRIPT_DIR/../../../"
elif [ -d "$SCRIPT_DIR/../../src/qwenpaw" ]; then
    QWENPAW_PATH="$SCRIPT_DIR/../../"
elif [ -d "$SCRIPT_DIR/../src/qwenpaw" ]; then
    QWENPAW_PATH="$SCRIPT_DIR/../"
fi


# 查找数据库文件
DB_PATH=""
if [ -n "$QWENPAW_PATH" ]; then
    # 在QwenPaw工作目录中查找
    for db in "$QWENPAW_PATH"/*/memory/human_thinking_memory_*.db; do
        if [ -f "$db" ]; then
            DB_PATH="$db"
            break
        fi
    done
fi

# 交互式输入数据库路径
if [ -z "$DB_PATH" ]; then
    echo ""
    echo "未找到数据库文件"
    echo "请输入数据库文件路径（按回车跳过，将只执行代码升级）:"
    read -r DB_PATH_INPUT
    DB_PATH="$DB_PATH_INPUT"
fi

# 创建备份目录
BACKUP_DIR="$SCRIPT_DIR/backups"
mkdir -p "$BACKUP_DIR"

# 备份旧版本（如果存在）
if [ -d "$SCRIPT_DIR/HumanThinkingMemoryManager" ]; then
    echo ""
    echo "1. 备份旧版本..."
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    tar -czf "$BACKUP_FILE" HumanThinkingMemoryManager
    echo "已备份旧版本到: $BACKUP_FILE"
fi

# 更新代码
echo ""
echo "2. 更新代码..."
if command -v git &> /dev/null; then
    cd "$SCRIPT_DIR"
    if git pull origin main &> /dev/null; then
        echo "已从GitHub拉取最新代码"
    else
        echo "Git拉取失败，请手动更新代码"
    fi
else
    echo "未安装git，请手动更新代码"
fi

# 升级数据库
if [ -n "$DB_PATH" ] && [ -f "$DB_PATH" ]; then
    echo ""
    echo "3. 升级数据库..."
    echo "数据库文件: $DB_PATH"
    echo "备份目录: $BACKUP_DIR"

    # 使用Python脚本升级数据库
    if [ -f "$SCRIPT_DIR/upgrade.py" ]; then
        $PYTHON_CMD "$SCRIPT_DIR/upgrade.py" --db-path "$DB_PATH" --backup-dir "$BACKUP_DIR"
    else
        echo "警告: 升级脚本不存在，跳过数据库升级"
    fi
else
    echo ""
    echo "3. 跳过数据库升级（未指定数据库文件）"
fi

# 安装到 QwenPaw
echo ""
echo "4. 安装到 QwenPaw..."
if [ -n "$QWENPAW_PATH" ]; then
    TOOLS_DIR="$QWENPAW_PATH/src/qwenpaw/agents/tools"
    mkdir -p "$TOOLS_DIR"

    # 复制核心文件
    cp -r "$SCRIPT_DIR/core" "$TOOLS_DIR/"
    cp -r "$SCRIPT_DIR/search" "$TOOLS_DIR/"
    cp -r "$SCRIPT_DIR/hooks" "$TOOLS_DIR/"
    cp -r "$SCRIPT_DIR/utils" "$TOOLS_DIR/"
    cp -r "$SCRIPT_DIR/config" "$TOOLS_DIR/"

    # 复制脚本文件
    cp "$SCRIPT_DIR/install.sh" "$TOOLS_DIR/"
    cp "$SCRIPT_DIR/uninstall.sh" "$TOOLS_DIR/"
    cp "$SCRIPT_DIR/upgrade.sh" "$TOOLS_DIR/"
    cp "$SCRIPT_DIR/upgrade.py" "$TOOLS_DIR/"

    echo "已安装到 QwenPaw tools 目录: $TOOLS_DIR"
else
    echo "未找到 QwenPaw 目录，跳过安装"
fi

echo ""
echo "=================================="
echo "升级完成！"
echo "目标版本: 1.0.2-beta0.3"
echo ""
echo "新功能："
echo "- 记忆温度概念：综合考虑访问频率、重要性、时间衰减"
echo "- 固定记忆机制：保护重要记忆不被自动降级"
echo "- 热数据/冷数据分层存储优化"
echo "- HNSW-like向量搜索算法"
echo "- 增量索引更新"
echo ""
echo "请重启 QwenPaw 以应用更改"
echo "=================================="
