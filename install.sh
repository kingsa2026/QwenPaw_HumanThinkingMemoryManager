#!/bin/bash

# Human Thinking Memory Manager 安装脚本
# 安装 Human Thinking Memory Manager 到 QwenPaw

echo "=== Human Thinking Memory Manager 安装脚本 ==="
echo "安装 Human Thinking Memory Manager 到 QwenPaw"

# 获取脚本所在目录
SCRIPT_DIR=$(dirname "$0")

# 计算 QwenPaw 路径
# 假设脚本位于 HumanThinkingMemoryManager 目录中，上级目录是 QwenPaw 的 tools 目录
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

# 创建目录
mkdir -p "$HUMAN_THINKING_DIR"

# 复制 Human Thinking Memory Manager 文件
echo "复制 Human Thinking Memory Manager 文件..."
cp -r "$SCRIPT_DIR/"* "$HUMAN_THINKING_DIR/"

# 复制时排除安装和卸载脚本
rm -f "$HUMAN_THINKING_DIR/install.sh"
rm -f "$HUMAN_THINKING_DIR/uninstall.sh"

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

echo "1. 修改 _resolve_memory_class 函数..."

# 修改 _resolve_memory_class 函数
OLD_FUNCTION="def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    raise ConfigurationException(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    )"

NEW_FUNCTION="def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n    from ...agents.tools.HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    elif backend == \"human_thinking\":\n        return HumanThinkingMemoryManager\n    raise ConfigurationException(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    )"

# 使用 sed 替换函数
sed -i "s|$OLD_FUNCTION|$NEW_FUNCTION|g" "$WORKSPACE_FILE"

echo "2. 修改 config.py 文件..."

# 修改 config.py 文件中的 memory_manager_backend 选项
OLD_CONFIG="memory_manager_backend: Literal[\"remelight\"] = Field(\n        default=\"remelight\",\n        description=(\n            \"Memory manager backend type. \"\n            \"Currently only 'remelight' is supported.\"\n        ),\n    )"

NEW_CONFIG="memory_manager_backend: Literal[\"remelight\", \"human_thinking\"] = Field(\n        default=\"remelight\",\n        description=(\n            \"Memory manager backend type. \"\n            \"Supported backends: 'remelight', 'human_thinking'.\"\n        ),\n    )"

# 使用 sed 替换配置
sed -i "s|$OLD_CONFIG|$NEW_CONFIG|g" "$CONFIG_FILE"

echo "3. 安装完成！"
echo "\n=== 安装完成 ==="
echo "Human Thinking Memory Manager 已成功安装到 QwenPaw"
echo "\n使用方法："
echo "1. 启动 QwenPaw"
echo "2. 进入 运行配置 页面"
echo "3. 在 记忆管理 部分，选择 'human_thinking' 作为记忆管理后端"
echo "4. 点击 保存 按钮"
echo "5. 重启 QwenPaw 服务以应用更改"
echo "\n或者，您可以在 config.py 中手动设置："
echo "memory_manager_backend = \"human_thinking\""
echo "\n默认情况下，系统仍会使用 'remelight' 作为记忆管理后端"
