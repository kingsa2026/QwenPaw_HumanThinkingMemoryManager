#!/bin/bash

# Human Thinking Memory Manager 安装脚本
# 用于将 Human Thinking Memory Manager 集成到 QwenPaw 中

set -e

echo "=== Human Thinking Memory Manager 安装脚本 ==="

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "脚本目录: $SCRIPT_DIR"

# 自动查找QwenPaw根目录
find_qwenpaw_root() {
    local search_path="$1"
    local max_depth=5

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

    # 尝试环境变量 QWENPAW_ROOT
    if [ -n "$QWENPAW_ROOT" ] && [ -d "$QWENPAW_ROOT/src/qwenpaw" ]; then
        echo "$QWENPAW_ROOT"
        return 0
    fi

    # 尝试常见位置（按优先级排序）
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

# 确定QwenPaw路径
if [ $# -gt 0 ]; then
    QwenPaw_PATH="$1"
    echo "使用命令行指定的路径: $QwenPaw_PATH"
else
    echo "正在自动查找QwenPaw根目录..."
    if [ -d "./src/qwenpaw" ] && [ -f "./pyproject.toml" ]; then
        QwenPaw_PATH="$(pwd)"
        echo "在当前目录找到QwenPaw: $QwenPaw_PATH"
    else
        QwenPaw_PATH=$(find_qwenpaw_root "$SCRIPT_DIR")
        if [ -z "$QwenPaw_PATH" ]; then
            echo "错误: 无法找到QwenPaw根目录"
            echo ""
            echo "请使用以下方式之一指定QwenPaw路径:"
            echo "1. 在QwenPaw根目录运行此脚本:"
            echo "   cd /path/to/QwenPaw"
            echo "   bash /path/to/install.sh"
            echo ""
            echo "2. 将HumanThinkingMemoryManager复制到QwenPaw后运行:"
            echo "   cp -r HumanThinkingMemoryManager QwenPaw/src/qwenpaw/agents/tools/"
            echo "   cd QwenPaw && bash src/qwenpaw/agents/tools/HumanThinkingMemoryManager/install.sh"
            echo ""
            echo "3. 使用命令行参数指定路径:"
            echo "   bash install.sh /path/to/QwenPaw"
            echo ""
            echo "4. 设置环境变量:"
            echo "   export QWENPAW_ROOT=/path/to/QwenPaw"
            echo "   bash install.sh"
            exit 1
        fi
        echo "自动找到QwenPaw: $QwenPaw_PATH"
    fi
fi

# 验证找到的路径
if [ ! -d "$QwenPaw_PATH/src/qwenpaw" ]; then
    echo "错误: 指定的路径不是有效的QwenPaw根目录"
    echo "未找到: $QwenPaw_PATH/src/qwenpaw"
    exit 1
fi

if [ ! -f "$QwenPaw_PATH/pyproject.toml" ]; then
    echo "错误: 指定的路径不是有效的QwenPaw根目录"
    echo "未找到: $QwenPaw_PATH/pyproject.toml"
    exit 1
fi

echo ""
echo "✓ QwenPaw根目录: $QwenPaw_PATH"
echo "✓ 脚本目录: $SCRIPT_DIR"

# 1. 复制 HumanThinkingMemoryManager 到 tools 目录
echo ""
echo "1. 复制 HumanThinkingMemoryManager 到 tools 目录..."

TOOLS_DIR="$QwenPaw_PATH/src/qwenpaw/agents/tools"
TARGET_DIR="$TOOLS_DIR/HumanThinkingMemoryManager"

if [ -d "$TARGET_DIR" ]; then
    echo "   目标目录已存在，正在删除..."
    rm -rf "$TARGET_DIR"
fi

cp -r "$SCRIPT_DIR" "$TARGET_DIR"
echo "   ✓ 成功复制到: $TARGET_DIR"

# 2. 更新 workspace.py 文件
echo ""
echo "2. 更新 workspace.py 文件..."

WORKSPACE_FILE="$QwenPaw_PATH/src/qwenpaw/app/workspace/workspace.py"

if [ ! -f "$WORKSPACE_FILE" ]; then
    echo "错误: 未找到 $WORKSPACE_FILE"
    exit 1
fi

if grep -q "HumanThinkingMemoryManager" "$WORKSPACE_FILE" 2>/dev/null; then
    echo "   ✓ HumanThinkingMemoryManager 支持已经存在"
else
    cp "$WORKSPACE_FILE" "${WORKSPACE_FILE}.bak"
    
    python3 << 'PYTHON_SCRIPT'
import sys
import re

workspace_file = sys.argv[1]

with open(workspace_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 新的函数定义
new_function = '''def _resolve_memory_class(backend: str) -> type:
    """Return the memory manager class for the given backend name."""
    from ...agents.memory import ReMeLightMemoryManager
    try:
        from ...agents.tools.HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager
        return HumanThinkingMemoryManager
    except ImportError:
        pass
    if backend == "remelight":
        return ReMeLightMemoryManager
    raise ConfigurationException(
        message=f"Unsupported memory manager backend: '{backend}'",
    )'''

# 使用正则查找并替换
pattern = r'def _resolve_memory_class\(backend: str\) -> type:.*?raise ConfigurationException\(.*?\)'
match = re.search(pattern, content, re.DOTALL)

if match:
    content = content[:match.start()] + new_function + content[match.end():]
    with open(workspace_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("   ✓ 成功更新 workspace.py")
else:
    print("   ⚠ 未找到 _resolve_memory_class 函数")
PYTHON_SCRIPT
    python3 - "$WORKSPACE_FILE"
fi

echo ""
echo "=========================================="
echo "✓ 安装完成！"
echo "=========================================="
echo ""
echo "Human Thinking Memory Manager 已成功集成到 QwenPaw 中"
echo ""
echo "使用方法："
echo "1. 重启 QwenPaw 服务以应用更改"
echo "2. 系统将自动使用 HumanThinkingMemoryManager"
echo ""
echo "=========================================="
