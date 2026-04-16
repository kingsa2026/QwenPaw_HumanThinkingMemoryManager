#!/bin/bash
# Human Thinking Memory Manager 一键升级脚本
# 支持从任意旧版本升级到最新版本

set -e

echo "=================================="
echo "Human Thinking Memory Manager 升级脚本"
echo "目标版本: 1.0.2-beta0.3"
echo "=================================="

# 获取脚本目录
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

# 自动查找QwenPaw根目录（与install.sh相同的逻辑）
find_qwenpaw_root() {
    local search_path="$1"

    # 检查标准路径结构（QwenPaw源码目录）
    check_standard_layout() {
        local path="$1"
        if [ -d "$path/src/qwenpaw" ] && [ -f "$path/pyproject.toml" ]; then
            echo "$path"
            return 0
        fi
        return 1
    }

    # 如果直接传入的是有效路径
    if [ -d "$search_path/src/qwenpaw" ] && [ -f "$search_path/pyproject.toml" ]; then
        echo "$search_path"
        return 0
    fi

    # 向上搜索（最多5层）
    local current_path="$search_path"
    for i in {1..5}; do
        if check_standard_layout "$current_path"; then
            echo "$current_path"
            return 0
        fi
        current_path="$(dirname "$current_path")"
    done

    # 尝试环境变量
    if [ -n "$QWENPAW_WORKING_DIR" ] && [ -d "$QWENPAW_WORKING_DIR" ]; then
        local src_path="$QWENPAW_WORKING_DIR"
        for i in {1..3}; do
            if check_standard_layout "$src_path"; then
                echo "$src_path"
                return 0
            fi
            src_path="$(dirname "$src_path")"
        done
    fi

    if [ -n "$QWENPAW_ROOT" ] && [ -d "$QWENPAW_ROOT/src/qwenpaw" ]; then
        echo "$QWENPAW_ROOT"
        return 0
    fi

    # 尝试常见位置
    local common_paths=(
        "$HOME/.qwenpaw"
        "$HOME/.copaw"
        "$HOME/QwenPaw"
        "$HOME/qwenpaw"
        "$HOME/projects/qwenpaw"
        "/opt/QwenPaw"
        "/opt/qwenpaw"
        "/root/QwenPaw"
        "/root/qwenpaw"
        "/usr/local/QwenPaw"
        "/usr/local/qwenpaw"
    )

    for path in "${common_paths[@]}"; do
        if check_standard_layout "$path"; then
            echo "$path"
            return 0
        fi
    done

    return 1
}

# 检测QwenPaw路径
QWENPAW_PATH=""

# 首先检查当前目录
if [ -d "./src/qwenpaw" ] && [ -f "./pyproject.toml" ]; then
    QWENPAW_PATH="$(pwd)"
    echo "在当前目录找到QwenPaw: $QWENPAW_PATH"
else
    # 在脚本目录向上搜索
    QWENPAW_PATH=$(find_qwenpaw_root "$SCRIPT_DIR")
fi

if [ -z "$QWENPAW_PATH" ]; then
    echo ""
    echo "未找到QwenPaw目录，将只执行本地升级"
    echo ""
    QWENPAW_PATH=""
else
    echo "找到QwenPaw: $QWENPAW_PATH"
fi

# 查找数据库文件
DB_PATH=""
if [ -n "$QWENPAW_PATH" ]; then
    # 在QwenPaw工作目录中查找
    for db in "$QWENPAW_PATH"/.qwenpaw/memory/human_thinking_memory_*.db; do
        if [ -f "$db" ]; then
            DB_PATH="$db"
            break
        fi
    done

    # 尝试旧版本路径
    if [ -z "$DB_PATH" ]; then
        for db in "$QWENPAW_PATH"/memory/human_thinking_memory_*.db; do
            if [ -f "$db" ]; then
                DB_PATH="$db"
                break
            fi
        done
    fi
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
    echo ""
    echo "如需手动安装到QwenPaw，请运行:"
    echo "   bash install.sh"
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
