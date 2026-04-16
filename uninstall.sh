#!/bin/bash

# Human Thinking Memory Manager 卸载脚本
# 用于从 QwenPaw 中移除 Human Thinking Memory Manager

set -e

echo "=== Human Thinking Memory Manager 卸载脚本 ==="

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "脚本目录: $SCRIPT_DIR"

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
            echo "请使用以下方式指定路径:"
            echo "   bash uninstall.sh /path/to/QwenPaw"
            exit 1
        fi

        echo "自动找到QwenPaw: $QwenPaw_PATH"
    fi
fi

# 验证路径
if [ ! -d "$QwenPaw_PATH/src/qwenpaw" ]; then
    echo "错误: 指定的路径不是有效的QwenPaw根目录"
    exit 1
fi

echo ""
echo "✓ QwenPaw根目录: $QwenPaw_PATH"

# 1. 从 workspace.py 中移除 HumanThinkingMemoryManager 支持
echo ""
echo "1. 从 workspace.py 中移除 HumanThinkingMemoryManager 支持..."

WORKSPACE_FILE="$QwenPaw_PATH/src/qwenpaw/app/workspace/workspace.py"

if [ -f "$WORKSPACE_FILE" ]; then
    if grep -q "HumanThinkingMemoryManager" "$WORKSPACE_FILE" 2>/dev/null; then
        cp "$WORKSPACE_FILE" "${WORKSPACE_FILE}.bak"

        # 使用Python脚本来修改文件
        python3 << 'PYTHON_SCRIPT'
import sys
import re

workspace_file = sys.argv[1]

with open(workspace_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 原始的函数定义（不包含HumanThinkingMemoryManager）
new_function = '''def _resolve_memory_class(backend: str) -> type:
    """Return the memory manager class for the given backend name."""
    from ...agents.memory import ReMeLightMemoryManager
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
    print("   ✓ 成功从 workspace.py 中移除 HumanThinkingMemoryManager 支持")
else:
    print("   ⚠ 未找到 _resolve_memory_class 函数")
PYTHON_SCRIPT
        python3 - "$WORKSPACE_FILE"
    else
        echo "   ✓ HumanThinkingMemoryManager 支持已经不存在"
    fi
else
    echo "   警告: workspace.py 文件不存在"
fi

# 2. 删除 HumanThinkingMemoryManager 目录
echo ""
echo "2. 删除 HumanThinkingMemoryManager 目录..."

TARGET_DIR="$QwenPaw_PATH/src/qwenpaw/agents/tools/HumanThinkingMemoryManager"

if [ -d "$TARGET_DIR" ]; then
    # 检查是否是当前脚本所在目录
    if [ "$SCRIPT_DIR" = "$TARGET_DIR" ]; then
        echo "   ⚠ 警告: 正在从安装目录运行卸载脚本"
        echo "   请先切换到其他目录后再运行卸载脚本，或手动删除目录"
    else
        rm -rf "$TARGET_DIR"
        echo "   ✓ 已删除: $TARGET_DIR"
    fi
else
    echo "   ✓ HumanThinkingMemoryManager 目录不存在"
fi

echo ""
echo "=========================================="
echo "✓ 卸载完成！"
echo "=========================================="
echo ""
echo "Human Thinking Memory Manager 已成功从 QwenPaw 中移除"
echo ""
echo "如需重新安装，请运行:"
echo "   bash install.sh"
echo ""
echo "=========================================="
