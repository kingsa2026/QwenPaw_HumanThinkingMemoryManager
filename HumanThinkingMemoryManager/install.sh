#!/bin/bash

# Human Thinking Memory Manager 安装脚本
# 用于将 Human Thinking Memory Manager 集成到 QwenPaw 中

echo "=== Human Thinking Memory Manager 安装脚本 ==="

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 计算QwenPaw根目录
# 从HumanThinkingMemoryManager目录向上4级：tools → agents → qwenpaw → src → QwenPaw
QwenPaw_PATH="$(cd "$SCRIPT_DIR/../../../../" && pwd)"

echo "Script directory: $SCRIPT_DIR"
echo "QwenPaw path: $QwenPaw_PATH"

if [ ! -d "$SCRIPT_DIR" ]; then
    echo "错误: 未找到 HumanThinkingMemoryManager 目录，请确保将其放在 QwenPaw/src/qwenpaw/agents/tools/ 目录下"
    exit 1
fi

# 1. 更新 tools/__init__.py 文件
echo "1. 更新 tools/__init__.py 文件..."

INIT_FILE="$QwenPaw_PATH/src/qwenpaw/agents/tools/__init__.py"

# 检查是否已经导入 HumanThinkingTool
if grep -q "HumanThinkingTool" "$INIT_FILE"; then
    echo "   HumanThinkingTool 已经在 __init__.py 中导入"
else
    # 备份原文件
    cp "$INIT_FILE" "${INIT_FILE}.bak"
    
    # 添加导入语句
    sed -i '1i from .HumanThinkingMemoryManager import HumanThinkingTool, get_tool' "$INIT_FILE"
    
    # 更新 __all__ 列表
    if grep -q "__all__ = " "$INIT_FILE"; then
        sed -i '/__all__ = / s/\[/\[\n    "HumanThinkingTool",\n    "get_tool",/' "$INIT_FILE"
    else
        echo "\n__all__ = [\n    \"HumanThinkingTool\",\n    \"get_tool\"\n]" >> "$INIT_FILE"
    fi
    
    echo "   成功更新 tools/__init__.py 文件"
fi

# 2. 更新 react_agent.py 文件
echo "2. 更新 react_agent.py 文件..."

REACT_AGENT_FILE="$QwenPaw_PATH/src/qwenpaw/agents/react_agent.py"

# 检查是否已经导入 get_tool
if grep -q "get_tool" "$REACT_AGENT_FILE"; then
    echo "   get_tool 已经在 react_agent.py 中导入"
else
    # 备份原文件
    cp "$REACT_AGENT_FILE" "${REACT_AGENT_FILE}.bak"
    
    # 添加导入语句
    sed -i '/from .tools import (/ s/\)/,\n    get_tool,\n)/' "$REACT_AGENT_FILE"
    
    echo "   成功添加 get_tool 导入"
fi

# 检查是否已经添加 human_thinking 到 tool_functions
if grep -q '"human_thinking": get_tool()' "$REACT_AGENT_FILE"; then
    echo "   human_thinking 已经在 tool_functions 中添加"
else
    # 添加 human_thinking 到 tool_functions
    sed -i '/"get_token_usage": get_token_usage,/a\            "human_thinking": get_tool(),' "$REACT_AGENT_FILE"
    
    echo "   成功添加 human_thinking 到 tool_functions"
fi

# 检查是否已经添加安装/卸载逻辑
if grep -q "Installing Human Thinking Tool" "$REACT_AGENT_FILE"; then
    echo "   安装/卸载逻辑已经存在"
else
    # 备份原文件（如果还没有备份）
    if [ ! -f "${REACT_AGENT_FILE}.bak" ]; then
        cp "$REACT_AGENT_FILE" "${REACT_AGENT_FILE}.bak"
    fi
    
    # 替换工具注册循环
    OLD_LOOP='# Register only enabled tools\n        for tool_name, tool_func in tool_functions.items():\n            # If tool not in config, enable by default (backward compatibility)\n            if not enabled_tools.get(tool_name, True):\n                logger.debug("Skipped disabled tool: %s", tool_name)\n                continue'
    
    NEW_LOOP='# Register only enabled tools\n        for tool_name, tool_func in tool_functions.items():\n            # Get enable status\n            is_enabled = enabled_tools.get(tool_name, True)\n            \n            # Handle Human Thinking Tool installation/uninstallation\n            if tool_name == "human_thinking":\n                if is_enabled:\n                    logger.info("Installing Human Thinking Tool...")\n                    # Execute enable action\n                    import asyncio\n                    loop = asyncio.get_event_loop()\n                    enable_result = loop.run_until_complete(tool_func._run(action="enable"))\n                    logger.info(f"Human Thinking Tool installation result: {enable_result.content[0]['text']}")\n                else:\n                    logger.info("Uninstalling Human Thinking Tool...")\n                    # Execute disable action\n                    import asyncio\n                    loop = asyncio.get_event_loop()\n                    disable_result = loop.run_until_complete(tool_func._run(action="disable"))\n                    logger.info(f"Human Thinking Tool uninstallation result: {disable_result.content[0]['text']}")\n                    # Skip registration if disabled\n                    continue\n\n            # Skip other disabled tools\n            if not is_enabled:\n                logger.debug("Skipped disabled tool: %s", tool_name)\n                continue'
    
    # 使用临时文件进行替换
    temp_file=$(mktemp)
    cat "$REACT_AGENT_FILE" | sed "s|$OLD_LOOP|$NEW_LOOP|g" > "$temp_file"
    mv "$temp_file" "$REACT_AGENT_FILE"
    
    echo "   成功添加安装/卸载逻辑"
fi

# 3. 更新 workspace.py 文件，添加 HumanThinkingMemoryManager 支持
echo "3. 更新 workspace.py 文件..."

WORKSPACE_FILE="$QwenPaw_PATH/src/qwenpaw/app/workspace/workspace.py"

# 检查是否已经添加 HumanThinkingMemoryManager 支持
if grep -q "HumanThinkingMemoryManager" "$WORKSPACE_FILE"; then
    echo "   HumanThinkingMemoryManager 支持已经存在"
else
    # 备份原文件
    cp "$WORKSPACE_FILE" "${WORKSPACE_FILE}.bak"
    
    # 修改 _resolve_memory_class 函数
    OLD_FUNCTION="def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    raise ConfigurationException(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    )"
    
    NEW_FUNCTION="def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n    from ...agents.tools.HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    elif backend == \"human_thinking\":\n        return HumanThinkingMemoryManager\n    raise ConfigurationException(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    )"
    
    # 使用临时文件进行替换
    temp_file=$(mktemp)
    cat "$WORKSPACE_FILE" | sed "s|$OLD_FUNCTION|$NEW_FUNCTION|g" > "$temp_file"
    mv "$temp_file" "$WORKSPACE_FILE"
    
    echo "   成功添加 HumanThinkingMemoryManager 支持"
fi

# 4. 检查 config.py 文件
echo "4. 检查 config.py 文件..."

CONFIG_FILE="$QwenPaw_PATH/src/qwenpaw/config/config.py"

# 检查是否已经添加 human_thinking 配置
if grep -q '"human_thinking": BuiltinToolConfig(' "$CONFIG_FILE"; then
    echo "   human_thinking 配置已经存在"
else
    # 备份原文件
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
    
    # 添加 human_thinking 配置
    sed -i '/"get_token_usage": BuiltinToolConfig(/,/),/a\        "human_thinking": BuiltinToolConfig(\n            name="human_thinking",\n            enabled=True,\n            description="超级神经记忆系统+跨session碎片化记忆整合+神经元感知向量记忆检索架构",\n            icon="🧠",\n        ),' "$CONFIG_FILE"
    
    echo "   成功添加 human_thinking 配置"
fi

echo "\n=== 安装完成 ==="
echo "Human Thinking Tool 已成功集成到 QwenPaw 中"
echo "请重启 QwenPaw 服务以应用更改"
echo "\n使用方法："
echo "1. 在 QwenPaw 中，Human Thinking Tool 已默认启用"
echo "2. 可以在工具管理界面中手动启用/禁用"
echo "3. 要使用 HumanThinkingMemoryManager，请在配置文件中设置 memory_manager.backend = \"human_thinking\""
echo "4. 默认为 ReMeLightMemoryManager，确保系统稳定性"