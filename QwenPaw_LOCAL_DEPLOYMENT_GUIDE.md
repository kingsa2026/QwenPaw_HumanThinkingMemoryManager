# QwenPaw 本地部署指南

## 前置要求

- Python 3.10 - 3.13
- Git
- 足够的磁盘空间（约2-3GB用于依赖和模型）

## 部署步骤

### 1. 克隆 QwenPaw 仓库（如果还没有）

```bash
cd "e:\项目\Human Thinking Tools"
git clone https://github.com/agentscope-ai/QwenPaw.git
```

### 2. 创建虚拟环境（推荐）

```bash
cd QwenPaw
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装 QwenPaw

```bash
pip install -e .
```

或者安装开发版本：

```bash
pip install -e ".[dev]"
```

### 4. 配置 QwenPaw

#### 4.1 初始化配置

```bash
qwenpaw init
```

这会在当前目录创建一个 `config.json` 文件。

#### 4.2 配置示例 (config.json)

```json
{
  "agent_id": "my-agent",
  "agent_name": "My Agent",
  "llm": {
    "model": "qwen-plus",
    "api_key": "your-api-key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
  },
  "memory_manager_backend": "human_thinking",
  "channels": {
    "feishu": {
      "enabled": true,
      "app_id": "your-feishu-app-id",
      "app_secret": "your-feishu-app-secret"
    }
  }
}
```

### 5. 安装 HumanThinkingMemoryManager

```bash
# 进入项目目录
cd "e:\项目\Human Thinking Tools\QwenPaw_HumanThinkingMemoryManager"

# 运行安装脚本
bash install.sh
```

### 6. 启动 QwenPaw

```bash
# 方式1: 使用 CLI
qwenpaw start

# 方式2: 直接运行
python -m qwenpaw
```

### 7. 验证部署

启动后，访问 QwenPaw Web UI（通常在 http://localhost:18792）

检查：
- HumanThinkingMemoryManager 是否显示为可用记忆后端
- 运行配置页面是否显示 "human_thinking" 选项

## 常见问题

### Q1: pip install 失败

**解决方案**：
1. 确保 Python 版本在 3.10-3.13 之间
2. 使用国内镜像源：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e .
```

### Q2: 依赖安装时间过长

**解决方案**：
1. 确保网络连接稳定
2. 使用离线模式（如果有预下载的包）
3. 可以分开安装主要依赖：
```bash
pip install agentscope==1.0.18
pip install -e .
```

### Q3: 找不到 HumanThinkingMemoryManager

**解决方案**：
1. 确保 install.sh 已成功运行
2. 检查 workspace.py 中的导入路径是否正确
3. 手动设置环境变量：
```bash
export PYTHONPATH="e:\项目\Human Thinking Tools\QwenPaw\src:$PYTHONPATH"
```

### Q4: 数据库初始化失败

**解决方案**：
1. 检查写入权限
2. 手动创建数据库目录：
```bash
mkdir -p ~/.qwenpaw/memory
```

## 验证 HumanThinkingMemoryManager 功能

### 1. 基础测试

```bash
cd "e:\项目\Human Thinking Tools\QwenPaw_HumanThinkingMemoryManager"
python test_human_thinking_memory_manager.py
```

### 2. 飞书消息处理测试

```bash
python -c "
from hooks.feishu_message_parser import parse_feishu_message, is_important_feishu_message

# 测试JSON格式消息
content = '{\"title\": \"Test\", \"content\": [[{\"tag\": \"text\", \"text\": \"Hello\"}]]}'
info = parse_feishu_message(content)
print(f'Parsed: {info.content}')
print(f'Is Important: {is_important_feishu_message(content)}')
"
```

### 3. 跨session功能测试

```bash
python test_session_management.py
```

## 卸载 HumanThinkingMemoryManager

```bash
cd "e:\项目\Human Thinking Tools\QwenPaw_HumanThinkingMemoryManager"
bash uninstall.sh
```

## 获取帮助

- QwenPaw GitHub: https://github.com/agentscope-ai/QwenPaw
- HumanThinkingMemoryManager GitHub: https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager
