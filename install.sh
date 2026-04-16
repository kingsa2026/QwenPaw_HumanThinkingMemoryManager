#!/bin/bash

# Human Thinking Memory Manager 安装脚本
# 用于将 Human Thinking Memory Manager 集成到 QwenPaw 中

set -e

echo "=== Human Thinking Memory Manager 安装脚本 ==="

# 判断运行模式：管道模式还是文件模式
PIPE_MODE=0
if [ "$0" = "bash" ] || [ "$0" = "-bash" ] || [ "$0" = "/dev/fd/63" ] || [ ! -f "$0" ]; then
    PIPE_MODE=1
    echo "检测到管道运行模式"
fi

# 获取脚本目录或临时目录
if [ $PIPE_MODE -eq 1 ]; then
    # 管道模式：创建临时目录
    SCRIPT_DIR=$(mktemp -d -t qwenpaw-hmm-XXXXXX)
    echo "使用临时目录: $SCRIPT_DIR"
    cleanup() {
        rm -rf "$SCRIPT_DIR"
    }
    trap cleanup EXIT
    
    # 下载完整仓库
    echo "正在下载 Human Thinking Memory Manager..."
    if command -v git &> /dev/null; then
        git clone --depth 1 https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager.git "$SCRIPT_DIR"
    else
        # 如果没有git，使用curl下载tar.gz
        if command -v curl &> /dev/null; then
            curl -L https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/archive/refs/heads/main.tar.gz -o "$SCRIPT_DIR/repo.tar.gz"
            tar -xzf "$SCRIPT_DIR/repo.tar.gz" -C "$SCRIPT_DIR" --strip-components 1
            rm "$SCRIPT_DIR/repo.tar.gz"
        elif command -v wget &> /dev/null; then
            wget -O "$SCRIPT_DIR/repo.tar.gz" https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/archive/refs/heads/main.tar.gz
            tar -xzf "$SCRIPT_DIR/repo.tar.gz" -C "$SCRIPT_DIR" --strip-components 1
            rm "$SCRIPT_DIR/repo.tar.gz"
        else
            echo "错误: 既没有git，也没有curl或wget，请先下载仓库再运行"
            exit 1
        fi
    fi
    echo "下载完成"
else
    # 文件模式：正常获取脚本目录
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    echo "脚本目录: $SCRIPT_DIR"
fi

# 自动查找QwenPaw根目录
find_qwenpaw_root() {
    local search_path="$1"
    
    # 1. 首先检查当前目录
    if [ -d "$(pwd)/src/qwenpaw" ] && [ -f "$(pwd)/pyproject.toml" ]; then
        echo "$(pwd)"
        return 0
    fi

    # 2. 如果传入了搜索路径，先检查它
    if [ -n "$search_path" ] && [ -d "$search_path" ]; then
        if [ -d "$search_path/src/qwenpaw" ] && [ -f "$search_path/pyproject.toml" ]; then
            echo "$search_path"
            return 0
        fi
    fi

    # 3. 尝试环境变量 QWENPAW_ROOT（优先级最高）
    if [ -n "$QWENPAW_ROOT" ]; then
        if [ -d "$QWENPAW_ROOT/src/qwenpaw" ] && [ -f "$QWENPAW_ROOT/pyproject.toml" ]; then
            echo "$QWENPAW_ROOT"
            return 0
        fi
    fi

    # 4. 尝试环境变量 QWENPAW_WORKING_DIR
    if [ -n "$QWENPAW_WORKING_DIR" ]; then
        if [ -d "$QWENPAW_WORKING_DIR/src/qwenpaw" ] && [ -f "$QWENPAW_WORKING_DIR/pyproject.toml" ]; then
            echo "$QWENPAW_WORKING_DIR"
            return 0
        fi
        # 尝试向上查找2层
        local src_path="$QWENPAW_WORKING_DIR"
        local i=0
        while [ $i -lt 2 ]; do
            src_path="$(dirname "$src_path")"
            if [ "$src_path" = "/" ]; then
                break
            fi
            if [ -d "$src_path/src/qwenpaw" ] && [ -f "$src_path/pyproject.toml" ]; then
                echo "$src_path"
                return 0
            fi
            i=$((i + 1))
        done
    fi

    # 5. 尝试常见位置（快速检查）
    local common_paths="$HOME/.qwenpaw $HOME/.copaw $HOME/QwenPaw $HOME/qwenpaw /opt/QwenPaw /opt/qwenpaw /root/QwenPaw /root/qwenpaw"

    for path in $common_paths; do
        if [ -d "$path/src/qwenpaw" ] && [ -f "$path/pyproject.toml" ]; then
            echo "$path"
            return 0
        fi
    done

    # 6. 向上搜索（最多3层，避免卡住）
    if [ -n "$search_path" ] && [ -d "$search_path" ]; then
        local current_path="$search_path"
        local i=0
        while [ $i -lt 3 ]; do
            current_path="$(dirname "$current_path")"
            if [ "$current_path" = "/" ]; then
                break
            fi
            if [ -d "$current_path/src/qwenpaw" ] && [ -f "$current_path/pyproject.toml" ]; then
                echo "$current_path"
                return 0
            fi
            i=$((i + 1))
        done
    fi

    # 未找到
    return 1
}

# 确定QwenPaw路径
if [ $# -gt 0 ]; then
    QwenPaw_PATH="$1"
    echo "使用命令行指定的路径: $QwenPaw_PATH"
else
    echo "正在自动查找QwenPaw根目录..."
    # Use || true to prevent set -e from exiting when function returns non-zero
    QwenPaw_PATH=$(find_qwenpaw_root "$(pwd)") || true
    
    # 如果没找到源码目录，尝试查找pip安装的QwenPaw
    if [ -z "$QwenPaw_PATH" ]; then
        echo "未找到QwenPaw源码目录，正在查找pip安装的QwenPaw..."
        QwenPaw_PATH=$(python3 -c "import qwenpaw, os; print(os.path.dirname(qwenpaw.__file__))" 2>/dev/null) || true
    fi
    
    # 如果还是没找到，尝试查找虚拟环境中的QwenPaw
    if [ -z "$QwenPaw_PATH" ]; then
        echo "未找到pip安装的QwenPaw，正在查找虚拟环境..."
        # 查找常见的虚拟环境位置
        VENV_PATHS="$HOME/.qwenpaw/venv $HOME/.copaw/venv /root/.qwenpaw/venv /root/.copaw/venv"
        for venv in $VENV_PATHS; do
            if [ -d "$venv" ]; then
                # 查找site-packages中的qwenpaw
                QwenPaw_PATH=$(find "$venv/lib" -name "qwenpaw" -type d -path "*/site-packages/qwenpaw" 2>/dev/null | head -1)
                if [ -n "$QwenPaw_PATH" ]; then
                    break
                fi
            fi
        done
    fi
    
    if [ -z "$QwenPaw_PATH" ]; then
        echo ""
        echo "❌ 错误: 无法找到QwenPaw根目录"
        echo ""
        echo "请使用以下方式之一指定QwenPaw路径:"
        echo ""
        echo "1. 在QwenPaw根目录运行此脚本:"
        echo "   cd /path/to/QwenPaw"
        echo "   bash /path/to/install.sh"
        echo ""
        echo "2. 使用命令行参数指定路径:"
        echo "   bash install.sh /path/to/QwenPaw"
        echo ""
        echo "3. 设置环境变量:"
        echo "   export QWENPAW_ROOT=/path/to/QwenPaw"
        echo "   bash install.sh"
        echo ""
        echo "4. 如果是pip安装的QwenPaw，可以指定Python包路径:"
        echo "   bash install.sh \$(python3 -c 'import qwenpaw, os; print(os.path.dirname(qwenpaw.__file__))')"
        exit 1
    fi
    echo "✓ 自动找到QwenPaw: $QwenPaw_PATH"
fi

# 验证找到的路径（支持源码和pip两种安装方式）
INSTALL_TYPE="source"
if [ -d "$QwenPaw_PATH/src/qwenpaw" ]; then
    # 源码安装方式
    QWENPAW_PKG_PATH="$QwenPaw_PATH/src/qwenpaw"
    INSTALL_TYPE="source"
    echo ""
    echo "✓ QwenPaw根目录: $QwenPaw_PATH"
    echo "✓ 安装类型: 源码方式"
elif [ -d "$QwenPaw_PATH" ] && [ -f "$QwenPaw_PATH/__init__.py" ]; then
    # pip安装方式（QwenPaw_PATH就是Python包目录）
    QWENPAW_PKG_PATH="$QwenPaw_PATH"
    INSTALL_TYPE="pip"
    echo ""
    echo "✓ QwenPaw包目录: $QwenPaw_PATH"
    echo "✓ 安装类型: pip方式"
else
    echo "错误: 指定的路径不是有效的QwenPaw目录"
    echo "未找到: $QwenPaw_PATH/src/qwenpaw 或 $QwenPaw_PATH/__init__.py"
    exit 1
fi

echo "✓ 脚本目录: $SCRIPT_DIR"

# 1. 复制 HumanThinkingMemoryManager 到 tools 目录
echo ""
echo "1. 复制 HumanThinkingMemoryManager 到 tools 目录..."

TOOLS_DIR="$QWENPAW_PKG_PATH/agents/tools"
TARGET_DIR="$TOOLS_DIR/HumanThinkingMemoryManager"

if [ -d "$TARGET_DIR" ]; then
    echo "   目标目录已存在，正在删除..."
    rm -rf "$TARGET_DIR"
fi

cp -r "$SCRIPT_DIR" "$TARGET_DIR"
echo "   ✓ 成功复制到: $TARGET_DIR"

# 2. 更新 workspace.py 文件，添加 HumanThinkingMemoryManager 支持
echo ""
echo "2. 更新 workspace.py 文件..."

WORKSPACE_FILE="$QWENPAW_PKG_PATH/app/workspace/workspace.py"

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

# 新的函数定义 - 添加human_thinking选项
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

# 3. 更新 config.py 文件，添加 human_thinking 选项
echo ""
echo "3. 更新 config.py 文件..."

CONFIG_FILE="$QWENPAW_PKG_PATH/config/config.py"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 未找到 $CONFIG_FILE"
    exit 1
fi

if grep -q "human_thinking" "$CONFIG_FILE" 2>/dev/null; then
    echo "   ✓ human_thinking 选项已经存在"
else
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
    
    python3 << 'PYTHON_SCRIPT'
import sys
import re

config_file = sys.argv[1]

with open(config_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并替换 memory_manager_backend 的 Literal 类型
old_pattern = r'memory_manager_backend: Literal\["remelight"\]'
new_pattern = 'memory_manager_backend: Literal["remelight", "human_thinking"]'

if re.search(old_pattern, content):
    content = re.sub(old_pattern, new_pattern, content)
    # 同时更新描述
    content = content.replace(
        'Currently only \'remelight\' is supported.',
        'Memory manager backend type. Options: "remelight" (default), "human_thinking".'
    )
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("   ✓ 成功更新 config.py，添加 human_thinking 选项")
else:
    print("   ⚠ 未找到 memory_manager_backend 配置")
PYTHON_SCRIPT
    python3 - "$CONFIG_FILE"
fi

echo ""
echo "=========================================="
echo "✓ 安装完成！"
echo "=========================================="
echo ""
echo "Human Thinking Memory Manager 已成功集成到 QwenPaw 中"
echo ""
echo "使用方法："
echo "1. 在 config.json 或 workspace/agent.json 中设置："
echo "   \"memory_manager_backend\": \"human_thinking\""
echo ""
echo "2. 重启 QwenPaw 服务以应用更改"
echo ""
echo "注意："
echo "- 默认为 \"remelight\"，如需使用 HumanThinkingMemoryManager，请手动修改配置"
echo "- 如果导入失败，会自动回退到默认的 ReMeLightMemoryManager"
echo ""
echo "=========================================="
