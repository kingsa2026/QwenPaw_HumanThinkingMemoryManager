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

    # 检查标准路径结构
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
    if [ -n "$QWENPAW_ROOT" ] && [ -d "$QWENPAW_ROOT/src/qwenpaw" ]; then
        echo "$QWENPAW_ROOT"
        return 0
    fi

    # 尝试常见位置
    local common_paths=(
        "$HOME/qwenpaw"
        "$HOME/projects/qwenpaw"
        "/opt/qwenpaw"
        "/root/qwenpaw"
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
    # 命令行参数提供路径
    QwenPaw_PATH="$1"
    echo "使用命令行指定的路径: $QwenPaw_PATH"
else
    # 自动查找
    echo "正在自动查找QwenPaw根目录..."

    # 首先检查当前目录
    if [ -d "./src/qwenpaw" ] && [ -f "./pyproject.toml" ]; then
        QwenPaw_PATH="$(pwd)"
        echo "在当前目录找到QwenPaw: $QwenPaw_PATH"
    else
        # 在脚本目录向上搜索
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

# 1. 更新 tools/__init__.py 文件
echo ""
echo "1. 更新 tools/__init__.py 文件..."

INIT_FILE="$QwenPaw_PATH/src/qwenpaw/agents/tools/__init__.py"

# 检查文件是否存在
if [ ! -f "$INIT_FILE" ]; then
    echo "错误: 未找到 $INIT_FILE"
    exit 1
fi

# 检查是否已经导入 HumanThinkingTool
if grep -q "HumanThinkingTool" "$INIT_FILE" 2>/dev/null; then
    echo "   ✓ HumanThinkingTool 已经在 __init__.py 中导入"
else
    # 备份原文件
    cp "$INIT_FILE" "${INIT_FILE}.bak"

    # 添加导入语句
    sed -i '1i from .HumanThinkingMemoryManager import HumanThinkingTool, get_tool' "$INIT_FILE"

    # 更新 __all__ 列表
    if grep -q "__all__ = " "$INIT_FILE" 2>/dev/null; then
        sed -i '/__all__ = / s/\[/\[\\n    "HumanThinkingTool",\\n    "get_tool",/' "$INIT_FILE"
    else
        echo "__all__ = [\"HumanThinkingTool\", \"get_tool\"]" >> "$INIT_FILE"
    fi

    echo "   ✓ 成功更新 tools/__init__.py 文件"
fi

# 2. 更新 workspace.py 文件，添加 HumanThinkingMemoryManager 支持
echo ""
echo "2. 更新 workspace.py 文件..."

WORKSPACE_FILE="$QwenPaw_PATH/src/qwenpaw/app/workspace/workspace.py"

if [ ! -f "$WORKSPACE_FILE" ]; then
    echo "错误: 未找到 $WORKSPACE_FILE"
    exit 1
fi

# 检查是否已经添加 HumanThinkingMemoryManager 支持
if grep -q "HumanThinkingMemoryManager" "$WORKSPACE_FILE" 2>/dev/null; then
    echo "   ✓ HumanThinkingMemoryManager 支持已经存在"
else
    # 备份原文件
    cp "$WORKSPACE_FILE" "${WORKSPACE_FILE}.bak"

    # 检查 _resolve_memory_class 函数是否存在
    if grep -q "_resolve_memory_class" "$WORKSPACE_FILE" 2>/dev/null; then
        # 使用Python脚本来修改文件，避免sed转义问题
        python3 << 'PYTHON_SCRIPT'
import sys

workspace_file = sys.argv[1]

with open(workspace_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 旧的函数定义
old_function = '''def _resolve_memory_class(backend: str) -> type:
    """Return the memory manager class for the given backend name."""
    from ...agents.memory import ReMeLightMemoryManager

    if backend == "remelight":
        return ReMeLightMemoryManager
    raise ConfigurationException(
        message=f"Unsupported memory manager backend: '{backend}'",
    )'''

# 新的函数定义
new_function = '''def _resolve_memory_class(backend: str) -> type:
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

if old_function in content:
    content = content.replace(old_function, new_function)
    with open(workspace_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("   ✓ 成功添加 HumanThinkingMemoryManager 支持")
else:
    print("   ⚠ 未找到 _resolve_memory_class 函数，请手动检查")
PYTHON_SCRIPT
        WORKSPACE_FILE="$WORKSPACE_FILE"
        python3 "$WORKSPACE_FILE" 2>/dev/null || true
    else
        echo "   ⚠ 未找到 _resolve_memory_class 函数，请手动检查"
    fi
fi

# 3. 检查 config.py 文件
echo ""
echo "3. 检查 config.py 文件..."

CONFIG_FILE="$QwenPaw_PATH/src/qwenpaw/config/config.py"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "   ⚠ config.py 不存在，跳过"
else
    # 检查是否已经添加 human_thinking 配置
    if grep -q '"human_thinking":' "$CONFIG_FILE" 2>/dev/null; then
        echo "   ✓ human_thinking 配置已经存在"
    else
        # 备份原文件
        cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"

        # 使用Python脚本来修改文件
        python3 << 'PYTHON_SCRIPT'
import sys

config_file = sys.argv[1]

with open(config_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 添加配置项
config_addition = '''    "human_thinking": BuiltinToolConfig(
        name="human_thinking",
        enabled=True,
        description="超级神经记忆系统+跨session碎片化记忆整合+神经元感知向量记忆检索架构",
        icon="🧠",
    ),'''

# 在get_token_usage配置后添加
marker = '"get_token_usage": BuiltinToolConfig('
if marker in content:
    # 找到 get_token_usage 配置块并在其后添加
    idx = content.find(marker)
    # 找到这个配置块的结束位置
    search_start = idx
    paren_count = 0
    i = search_start
    while i < len(content):
        if content[i] == '(':
            paren_count += 1
        elif content[i] == ')':
            paren_count -= 1
            if paren_count == 0:
                # 找到了配置块的结束
                end_idx = i + 1
                # 在这里插入新配置
                content = content[:end_idx] + '\n        ' + config_addition + content[end_idx:]
                break
        i += 1

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("   ✓ 成功添加 human_thinking 配置")
else:
    print("   ⚠ 未找到 get_token_usage 配置，跳过")
PYTHON_SCRIPT
        CONFIG_FILE="$CONFIG_FILE"
        python3 "$CONFIG_FILE" 2>/dev/null || true
    fi
fi

echo ""
echo "=========================================="
echo "✓ 安装完成！"
echo "=========================================="
echo ""
echo "Human Thinking Tool 已成功集成到 QwenPaw 中"
echo ""
echo "使用方法："
echo "1. 在 QwenPaw 配置文件中设置:"
echo "   memory_manager.backend = 'human_thinking'"
echo ""
echo "2. 或者在UI中选择 human_thinking 作为记忆后端"
echo ""
echo "3. 重启 QwenPaw 服务以应用更改"
echo ""
echo "=========================================="
