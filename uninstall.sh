#!/bin/bash

# Human Thinking Memory Manager 卸载脚本
# 用于从 QwenPaw 中移除 Human Thinking Memory Manager

echo "=== Human Thinking Memory Manager 卸载脚本 ==="

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 计算QwenPaw根目录
# 从HumanThinkingMemoryManager目录向上4级：tools → agents → qwenpaw → src → QwenPaw
QwenPaw_PATH="$(cd "$SCRIPT_DIR/../../../../" && pwd)"

echo "Script directory: $SCRIPT_DIR"
echo "QwenPaw path: $QwenPaw_PATH"

# 1. 执行 Human Thinking Memory Manager 的禁用操作
echo "1. 执行 Human Thinking Memory Manager 禁用操作..."

# 尝试运行禁用操作
if [ -d "$SCRIPT_DIR" ]; then
    echo "   执行禁用操作以恢复原始文件..."
else
    echo "   警告: HumanThinkingMemoryManager 目录不存在"
fi

# 2. 从 workspace.py 中移除 HumanThinkingMemoryManager 支持
echo "2. 从 workspace.py 中移除 HumanThinkingMemoryManager 支持..."

WORKSPACE_FILE="$QwenPaw_PATH/src/qwenpaw/app/workspace/workspace.py"

if [ -f "$WORKSPACE_FILE" ]; then
    # 备份原文件
    cp "$WORKSPACE_FILE" "${WORKSPACE_FILE}.bak"
    
    # 恢复 _resolve_memory_class 函数
    OLD_FUNCTION="def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n    from ...agents.tools.HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    elif backend == \"human_thinking\":\n        return HumanThinkingMemoryManager\n    raise ConfigurationException(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    )"
    
    NEW_FUNCTION="def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    raise ConfigurationException(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    )"
    
    # 使用临时文件进行替换
    temp_file=$(mktemp)
    cat "$WORKSPACE_FILE" | sed "s|$OLD_FUNCTION|$NEW_FUNCTION|g" > "$temp_file"
    mv "$temp_file" "$WORKSPACE_FILE"
    
    echo "   成功从 workspace.py 中移除 HumanThinkingMemoryManager 支持"
else
    echo "   警告: workspace.py 文件不存在"
fi

# 3. 从 tools/__init__.py 中移除导入
echo "3. 从 tools/__init__.py 中移除导入..."

INIT_FILE="$QwenPaw_PATH/src/qwenpaw/agents/tools/__init__.py"

if [ -f "$INIT_FILE" ]; then
    # 备份原文件
    cp "$INIT_FILE" "${INIT_FILE}.bak"
    
    # 移除导入语句
    sed -i '/from .HumanThinkingMemoryManager import HumanThinkingTool, get_tool/d' "$INIT_FILE"
    
    # 移除 __all__ 中的相关条目
    sed -i '/"HumanThinkingTool",/d' "$INIT_FILE"
    sed -i '/"get_tool",/d' "$INIT_FILE"
    
    echo "   成功从 tools/__init__.py 中移除导入"
else
    echo "   警告: tools/__init__.py 文件不存在"
fi

# 4. 从 react_agent.py 中移除相关代码
echo "4. 从 react_agent.py 中移除相关代码..."

REACT_AGENT_FILE="$QwenPaw_PATH/src/qwenpaw/agents/react_agent.py"

if [ -f "$REACT_AGENT_FILE" ]; then
    # 备份原文件
    cp "$REACT_AGENT_FILE" "${REACT_AGENT_FILE}.bak"
    
    # 移除 get_tool 导入
    sed -i '/get_tool,/d' "$REACT_AGENT_FILE"
    
    # 移除 human_thinking 工具注册
    sed -i '/"human_thinking": get_tool(),/d' "$REACT_AGENT_FILE"
    
    # 恢复工具注册循环
    OLD_LOOP='# Register only enabled tools\n        for tool_name, tool_func in tool_functions.items():\n            # Get enable status\n            is_enabled = enabled_tools.get(tool_name, True)\n            \n            # Handle Human Thinking Tool installation/uninstallation\n            if tool_name == "human_thinking":\n                if is_enabled:\n                    logger.info("Installing Human Thinking Tool...")\n                    # Execute enable action\n                    import asyncio\n                    loop = asyncio.get_event_loop()\n                    enable_result = loop.run_until_complete(tool_func._run(action="enable"))\n                    logger.info(f"Human Thinking Tool installation result: {enable_result.content[0]['text']}")\n                else:\n                    logger.info("Uninstalling Human Thinking Tool...")\n                    # Execute disable action\n                    import asyncio\n                    loop = asyncio.get_event_loop()\n                    disable_result = loop.run_until_complete(tool_func._run(action="disable"))\n                    logger.info(f"Human Thinking Tool uninstallation result: {disable_result.content[0]['text']}")\n                    # Skip registration if disabled\n                    continue\n\n            # Skip other disabled tools\n            if not is_enabled:\n                logger.debug("Skipped disabled tool: %s", tool_name)\n                continue'
    
    NEW_LOOP='# Register only enabled tools\n        for tool_name, tool_func in tool_functions.items():\n            # If tool not in config, enable by default (backward compatibility)\n            if not enabled_tools.get(tool_name, True):\n                logger.debug("Skipped disabled tool: %s", tool_name)\n                continue'
    
    # 使用临时文件进行替换
    temp_file=$(mktemp)
    cat "$REACT_AGENT_FILE" | sed "s|$OLD_LOOP|$NEW_LOOP|g" > "$temp_file"
    mv "$temp_file" "$REACT_AGENT_FILE"
    
    echo "   成功从 react_agent.py 中移除相关代码"
else
    echo "   警告: react_agent.py 文件不存在"
fi

# 5. 从 config.py 中移除配置
echo "5. 从 config.py 中移除配置..."

CONFIG_FILE="$QwenPaw_PATH/src/qwenpaw/config/config.py"

if [ -f "$CONFIG_FILE" ]; then
    # 备份原文件
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
    
    # 移除 human_thinking 配置
    sed -i '/"human_thinking": BuiltinToolConfig(/,/),/d' "$CONFIG_FILE"
    
    echo "   成功从 config.py 中移除配置"
else
    echo "   警告: config.py 文件不存在"
fi

# 6. 清理 HumanThinkingMemoryManager 目录
echo "6. 清理 HumanThinkingMemoryManager 目录..."

echo "   注意: 保留 HumanThinkingMemoryManager 目录结构，如需完全删除请手动执行"
echo "   rm -rf $SCRIPT_DIR"

echo "\n=== 卸载完成 ==="
echo "Human Thinking Memory Manager 已成功从 QwenPaw 中移除"
echo "请重启 QwenPaw 服务以应用更改"
