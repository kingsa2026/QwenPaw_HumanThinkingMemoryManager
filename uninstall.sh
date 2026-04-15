#!/bin/bash

# Human Thinking Memory Manager 卸载脚本
# 从 QwenPaw 中移除 Human Thinking Memory Manager
echo "=== Human Thinking Memory Manager 卸载脚本 ==="
echo "从 QwenPaw 中移除 Human Thinking Memory Manager"

# 获取脚本所在目录
SCRIPT_DIR=$(dirname "$0")

# 计算 QwenPaw 路径
QwenPaw_PATH="$(cd "$SCRIPT_DIR/../../../" && pwd)"

echo "QwenPaw 路径: $QwenPaw_PATH"

# 检查 QwenPaw 目录是否存在
if [ ! -d "$QwenPaw_PATH" ]; then
    echo "错误: 未找到 QwenPaw 目录"
    exit 1
fi

# 检查 QwenPaw 源代码目录
if [ ! -d "$QwenPaw_PATH/src/qwenpaw" ]; then
    echo "错误: 未找到 QwenPaw 源代码目录"
    exit 1
fi

# 目标目录
TOOLS_DIR="$QwenPaw_PATH/src/qwenpaw/agents/tools"
HUMAN_THINKING_DIR="$TOOLS_DIR/HumanThinkingMemoryManager"

echo "目标目录: $HUMAN_THINKING_DIR"

echo "1. 执行 Human Thinking Memory Manager 禁用操作..."

# 检查 workspace.py 文件
WORKSPACE_FILE="$QwenPaw_PATH/src/qwenpaw/app/workspace/workspace.py"
if [ ! -f "$WORKSPACE_FILE" ]; then
    echo "错误: 未找到 workspace.py 文件"
    exit 1
fi

# 检查 config.py 文件
CONFIG_FILE="$QwenPaw_PATH/src/qwenpaw/config/config.py"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 未找到 config.py 文件"
    exit 1
fi

# 恢复 _resolve_memory_class 函数
NEW_FUNCTION="def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n    from ...agents.tools.HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    elif backend == \"human_thinking\":\n        return HumanThinkingMemoryManager\n    raise ConfigurationException(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    )"

OLD_FUNCTION="def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    raise ConfigurationException(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    )"

# 使用 sed 恢复函数
sed -i "s|$NEW_FUNCTION|$OLD_FUNCTION|g" "$WORKSPACE_FILE"

echo "2. 恢复 config.py 文件..."

# 恢复 config.py 文件中的 memory_manager_backend 选项
NEW_CONFIG="memory_manager_backend: Literal[\"remelight\", \"human_thinking\"] = Field(\n        default=\"remelight\",\n        description=(\n            \"Memory manager backend type. \"\n            \"Supported backends: 'remelight', 'human_thinking'.\"\n        ),\n    )"

OLD_CONFIG="memory_manager_backend: Literal[\"remelight\"] = Field(\n        default=\"remelight\",\n        description=(\n            \"Memory manager backend type. \"\n            \"Currently only 'remelight' is supported.\"\n        ),\n    )"

# 使用 sed 恢复配置
sed -i "s|$NEW_CONFIG|$OLD_CONFIG|g" "$CONFIG_FILE"

echo "3. 删除 Human Thinking Memory Manager 目录..."

# 删除 Human Thinking Memory Manager 目录
if [ -d "$HUMAN_THINKING_DIR" ]; then
    rm -rf "$HUMAN_THINKING_DIR"
    echo "已删除 Human Thinking Memory Manager 目录"
else
    echo "Human Thinking Memory Manager 目录不存在"
fi

echo "\n=== 卸载完成 ==="
echo "Human Thinking Memory Manager 已成功从 QwenPaw 中移除"
echo "\n注意："
echo "1. 系统将恢复使用 'remelight' 作为默认记忆管理后端"
echo "2. 请重启 QwenPaw 服务以应用更改"
echo "3. 您的记忆数据将保持不变，只是管理方式会切换回默认的 ReMeLightMemoryManager"
