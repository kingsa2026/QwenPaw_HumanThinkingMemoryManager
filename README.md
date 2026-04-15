# QwenPaw Human Thinking Memory Manager

Human Thinking Memory Manager 是 QwenPaw 的一个高级记忆管理插件，提供类人记忆管理功能，包括记忆冷藏/解冻机制、动态重要性标记、多模态检索和记忆固化与迁移。

## 功能特性

- **SQLite 本地存储**：支持向量检索的本地数据库存储
- **记忆冷藏/解冻机制**：自动识别和冷藏低频访问记忆，需要时解冻
- **动态重要性标记**：根据访问频率和内容重要性自动标记记忆
- **多模态检索**：支持文本和向量混合检索
- **记忆固化与迁移**：支持从旧格式（MEMORY.md, memory.json）迁移到新的SQLite格式
- **版本管理**：支持数据库结构升级和备份

## 安装方法

### 手动安装

1. 克隆本仓库：
   ```bash
   git clone https://github.com/yourusername/QwenPaw_HumanThinkingMemoryManager.git
   ```

2. 将 `HumanThinkingMemoryManager` 文件夹复制到 QwenPaw 的 `src/qwenpaw/agents/tools/` 目录下：
   ```bash
   cp -r HumanThinkingMemoryManager /path/to/QwenPaw/src/qwenpaw/agents/tools/
   ```

3. 运行安装脚本：
   ```bash
   cd /path/to/QwenPaw/src/qwenpaw/agents/tools/HumanThinkingMemoryManager
   chmod +x install.sh
   ./install.sh
   ```

### 使用方法

1. 在 QwenPaw 配置文件中启用 HumanThinkingMemoryManager：
   ```python
   # 在 config.py 中设置
   memory_manager.backend = "human_thinking"
   ```

2. 重启 QwenPaw 服务以应用更改。

## 配置选项

### 嵌入配置

HumanThinkingMemoryManager 支持使用外部嵌入模型进行向量检索。可以在 `config.py` 中配置：

```python
# 嵌入配置
embedding_config = {
    "backend": "openai",  # 支持 openai, azure, ollama 等
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1",
    "model_name": "text-embedding-3-small",
    "dimensions": 1536,
    "enable_cache": True,
    "use_dimensions": True,
    "max_cache_size": 10000,
    "max_input_length": 8191,
    "max_batch_size": 100
}
```

### 环境变量

也可以通过环境变量配置嵌入模型：

- `EMBEDDING_API_KEY`：嵌入模型的 API 密钥
- `EMBEDDING_BASE_URL`：嵌入模型的 API 基础 URL
- `EMBEDDING_MODEL_NAME`：嵌入模型的名称

## 目录结构

```
HumanThinkingMemoryManager/
├── core/              # 核心模块
│   ├── __init__.py
│   ├── database.py     # 数据库操作
│   └── memory_manager.py  # 记忆管理器
├── search/            # 搜索模块
│   ├── __init__.py
│   └── vector.py      # 向量搜索
├── hooks/             # 钩子模块
│   ├── __init__.py
│   └── memory_hooks.py  # 记忆钩子
├── utils/             # 工具模块
│   ├── __init__.py
│   ├── migrator.py     # 数据迁移
│   └── version.py      # 版本管理
├── config/            # 配置模块
│   ├── __init__.py
│   └── config.py       # 配置管理
├── __init__.py        # 模块初始化
├── install.sh         # 安装脚本
├── uninstall.sh       # 卸载脚本
└── README.md          # 文档
```

## 核心功能

### 记忆存储

```python
# 存储记忆
memory_id = await memory_manager.store_memory(
    content="这是一段记忆内容",
    source_id="user",
    session_id="session_123",
    importance=4,  # 1-5，5最重要
    metadata={"entity_name": "张三", "entity_type": "person"}
)
```

### 记忆搜索

```python
# 搜索记忆
result = await memory_manager.memory_search(
    query="张三的信息",
    max_results=5,
    min_score=0.1
)
```

### 记忆冷藏/解冻

```python
# 冷藏低频访问记忆
frozen_count = await memory_manager.freeze_memories()

# 解冻与查询相关的记忆
defrosted_count = await memory_manager.defrost_memories("张三")
```

### 记忆统计

```python
# 获取记忆统计信息
stats = memory_manager.get_stats()
print(stats)
```

## 注意事项

1. **数据库备份**：在数据库结构升级时，系统会自动备份旧数据库，确保数据安全。

2. **性能优化**：对于大量记忆，建议配置外部嵌入模型以提高搜索性能。

3. **内存使用**：默认情况下，系统会自动管理内存使用，冷藏低频访问的记忆。

4. **兼容性**：HumanThinkingMemoryManager 与 QwenPaw 的默认 ReMeLightMemoryManager 完全兼容，可以随时切换。

## 卸载方法

运行卸载脚本：

```bash
cd /path/to/QwenPaw/src/qwenpaw/agents/tools/HumanThinkingMemoryManager
chmod +x uninstall.sh
./uninstall.sh
```

然后将 `memory_manager.backend` 改回 `remelight` 以使用默认的记忆管理器。

## 版本历史

- v1.0.0：初始版本，支持基本的记忆管理功能

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 许可证

MIT License
