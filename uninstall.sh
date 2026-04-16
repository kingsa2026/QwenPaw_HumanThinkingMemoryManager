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

# 1. 执行 Human Thinking Memory Manager 的禁用操作
echo ""
echo "1. 执行 Human Thinking Memory Manager 禁用操作..."

if [ -d "$SCRIPT_DIR" ]; then
    echo "   执行禁用操作以恢复原始文件..."
else
    echo "   警告: HumanThinkingMemoryManager 目录不存在"
fi

# 2. 从 workspace.py 中移除 HumanThinkingMemoryManager 支持
echo ""
echo "2. 从 workspace.py 中移除 HumanThinkingMemoryManager 支持..."

WORKSPACE_FILE="$QwenPaw_PATH/src/qwenpaw/app/workspace/workspace.py"

if [ -f "$WORKSPACE_FILE" ]; then
    # 检查是否已经包含HumanThinkingMemoryManager
    if grep -q "HumanThinkingMemoryManager" "$WORKSPACE_FILE" 2>/dev/null; then
        # 备份原文件
        cp "$WORKSPACE_FILE" "${WORKSPACE_FILE}.bak"

        # 使用Python脚本来修改文件
        python3 << 'PYTHON_SCRIPT'
import sys

workspace_file = sys.argv[1]

with open(workspace_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 当前的函数定义（包含HumanThinkingMemoryManager）
old_function = '''def _resolve_memory_class(backend: str) -> type:
    """Return the memory manager class for the given backend name."""
    from ...agents.memory import ReMeLightMemoryManager
    try:
        from ...agents.tools.HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager
    except ImportError:
        HumanThinkingMemoryManager = None

    if backend == "remelight":
        return ReMeLightMemoryManager
    elif backend == "human_thinking" and HumanThinkingMemoryManager is not None:
        return HumanThinkingMemoryManager
    raise ConfigurationException(
        message=f"Unsupported memory manager backend: '{backend}'",
    )'''

# 原始的函数定义（不包含HumanThinkingMemoryManager）
new_function = '''def _resolve_memory_class(backend: str) -> type:
    """Return the memory manager class for the given backend name."""
    from ...agents.memory import ReMeLightMemoryManager

    if backend == "remelight":
        return ReMeLightMemoryManager
    raise ConfigurationException(
        message=f"Unsupported memory manager backend: '{backend}'",
    )'''

if old_function in content:
    content = content.replace(old_function, new_function)
    with open(workspace_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("   ✓ 成功从 workspace.py 中移除 HumanThinkingMemoryManager 支持")
else:
    print("   ⚠ 未找到 HumanThinkingMemoryManager 相关代码，可能已经被移除")
PYTHON_SCRIPT
        WORKSPACE_FILE="$WORKSPACE_FILE"
        python3 "$WORKSPACE_FILE" 2>/dev/null || true
    else
        echo "   ✓ HumanThinkingMemoryManager 支持已经不存在"
    fi
else
    echo "   警告: workspace.py 文件不存在"
fi

# 3. 从 tools/__init__.py 中移除导入
echo ""
echo "3. 从 tools/__init__.py 中移除 HumanThinkingTool 导入..."

INIT_FILE="$QwenPaw_PATH/src/qwenpaw/agents/tools/__init__.py"

if [ -f "$INIT_FILE" ]; then
    if grep -q "HumanThinkingTool" "$INIT_FILE" 2>/dev/null; then
        cp "$INIT_FILE" "${INIT_FILE}.bak"

        # 移除导入行
        sed -i '/from .HumanThinkingMemoryManager import/d' "$INIT_FILE"
        sed -i '/"HumanThinkingTool"/d' "$INIT_FILE"
        sed -i '/"get_tool"/d' "$INIT_FILE"

        echo "   ✓ 成功从 tools/__init__.py 中移除导入"
    else
        echo "   ✓ HumanThinkingTool 导入已经不存在"
    fi
else
    echo "   警告: tools/__init__.py 文件不存在"
fi

# 4. 从 config.py 中移除配置
echo ""
echo "4. 从 config.py 中移除 human_thinking 配置..."

CONFIG_FILE="$QwenPaw_PATH/src/qwenpaw/config/config.py"

if [ -f "$CONFIG_FILE" ]; then
    if grep -q '"human_thinking":' "$CONFIG_FILE" 2>/dev/null; then
        cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"

        # 使用Python脚本移除配置块
        python3 << 'PYTHON_SCRIPT'
import sys

config_file = sys.argv[1]

with open(config_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并移除 human_thinking 配置块
marker = '"human_thinking": BuiltinToolConfig('
if marker in content:
    idx = content.find(marker)
    # 找到配置块的结束位置
    search_start = idx
    paren_count = 0
    i = search_start
    while i < len(content):
        if content[i] == '(':
            paren_count += 1
        elif content[i] == ')':
            paren_count -= 1
            if paren_count == 0:
                end_idx = i + 1
                # 移除整个配置块（包括前面的逗号和空白）
                # 向前查找逗号
                j = idx - 1
                while j >= 0 and content[j] in ' \t\n':
                    j -= 1
                if j >= 0 and content[j] == ',':
                    idx = j
                # 移除
                content = content[:idx] + content[end_idx:]
                break
        i += 1

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("   ✓ 成功从 config.py 中移除 human_thinking 配置")
else:
    print("   ⚠ human_thinking 配置已经不存在")
PYTHON_SCRIPT
        CONFIG_FILE="$CONFIG_FILE"
        python3 "$CONFIG_FILE" 2>/dev/null || true
    else
        echo "   ✓ human_thinking 配置已经不存在"
    fi
else
    echo "   警告: config.py 文件不存在"
fi

echo ""
echo "=========================================="
echo "✓ 卸载完成！"
echo "=========================================="
echo ""
echo "Human Thinking Tool 已成功从 QwenPaw 中移除"
echo ""
echo "如需重新安装，请运行:"
echo "   bash install.sh"
echo ""
echo "=========================================="
