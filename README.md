# QwenPaw Human Thinking Memory Manager

Human Thinking Memory Manager 是 QwenPaw 的一个高级记忆管理插件，提供类人记忆管理功能，包括记忆冷藏/解冻机制、动态重要性标记、多模态检索和记忆固化与迁移。

## 核心亮点

### 1. SQLite 架构 - 轻量级且模拟真人记忆

- **无需额外依赖**：使用内置的 SQLite 数据库，无需安装外部数据库服务
- **本地存储**：所有记忆数据存储在本地，保证数据隐私和安全性
- **类人记忆模型**：模拟人类记忆的存储和检索机制，包括短期记忆和长期记忆
- **高效存储**：优化的数据库结构，支持快速存储和检索大量记忆
- **自动管理**：自动处理记忆的创建、更新和删除，无需手动干预

### 2. 模拟人类记忆检索机制

- **语义搜索**：使用向量嵌入技术实现语义理解，像人类一样理解记忆内容
- **关联检索**：基于记忆之间的关联关系进行检索，模拟人类的联想记忆
- **重要性排序**：根据记忆的重要性和访问频率进行排序，优先返回重要记忆
- **上下文感知**：考虑当前上下文进行检索，提高检索准确性
- **模糊匹配**：支持部分匹配和近似匹配，模拟人类的模糊记忆

### 3. 解决 Agent 跨 Session 失忆问题

- **持久化存储**：记忆在会话之间持久化存储，不会因为会话结束而丢失
- **会话关联**：自动关联不同会话中的相关记忆，形成完整的记忆链
- **跨会话检索**：在新会话中可以检索到之前会话的记忆
- **记忆整合**：自动整合跨会话的相关记忆，形成连贯的记忆体系
- **Agent 内部沟通**：解决了 QwenPaw 中 Agent 之间无法共享记忆的痛点，实现 Agent 间的记忆传递

## 技术说明

### 核心架构

Human Thinking Memory Manager 采用模块化设计，由以下核心组件组成：

- **核心模块 (core)**：包含记忆管理器和数据库操作
- **搜索模块 (search)**：提供向量搜索和后备搜索功能
- **钩子模块 (hooks)**：实现记忆检索、写入和冷藏/解冻钩子
- **工具模块 (utils)**：包含数据迁移和版本管理工具
- **配置模块 (config)**：管理插件配置

### 数据库结构

Human Thinking Memory Manager 使用 SQLite 数据库存储记忆，数据库结构设计如下：

#### 主要表结构

1. **memories 表**
   - `id`：记忆唯一标识符
   - `content`：记忆内容
   - `source_id`：记忆来源
   - `session_id`：会话 ID
   - `importance`：重要性级别 (1-5)
   - `entity_name`：实体名称
   - `entity_type`：实体类型
   - `created_at`：创建时间
   - `updated_at`：更新时间
   - `last_accessed_at`：最后访问时间
   - `frozen`：是否被冷藏

2. **embeddings 表**
   - `id`：嵌入唯一标识符
   - `memory_id`：关联的记忆 ID
   - `embedding`：向量嵌入数据
   - `created_at`：创建时间

3. **versions 表**
   - `key`：版本键
   - `value`：版本值
   - `description`：版本描述
   - `created_at`：创建时间

4. **migration_history 表**
   - `id`：迁移记录 ID
   - `version`：迁移版本
   - `date`：迁移日期
   - `description`：迁移描述

### 设计亮点

1. **动态路径解析**：使用 `__file__` 动态计算模块路径，确保无论模块放在哪里都能正确导入
2. **模块化设计**：清晰的模块划分，便于维护和扩展
3. **自动版本管理**：内置版本管理机制，支持数据库结构升级
4. **数据迁移**：支持从旧格式（MEMORY.md, memory.json）迁移到新的 SQLite 格式
5. **记忆冷藏/解冻**：智能识别和管理低频访问记忆
6. **向量检索**：支持使用外部嵌入模型进行语义搜索
7. **多模态支持**：为未来的多模态记忆管理做准备

## 功能优势

### 1. 智能记忆管理

- **记忆重要性评估**：根据访问频率和内容自动评估记忆重要性
- **记忆冷藏机制**：自动冷藏低频访问的记忆，优化存储空间
- **记忆解冻机制**：当需要时自动解冻相关记忆

### 2. 高效检索

- **向量搜索**：使用嵌入模型进行语义搜索，提高搜索准确性
- **混合检索**：结合文本和向量检索，提供更全面的搜索结果
- **实时更新**：搜索后自动更新记忆的访问时间

### 3. 数据安全

- **自动备份**：在数据库结构升级时自动备份旧数据库
- **版本管理**：详细的版本历史记录，支持回滚
- **数据迁移**：安全地从旧格式迁移到新格式

### 4. 扩展性

- **插件架构**：作为 QwenPaw 的插件，易于集成
- **可配置性**：支持通过配置文件和环境变量进行配置
- **模块化设计**：便于添加新功能和改进现有功能

## 安装方法

### 一键安装（推荐）

使用提供的一键安装脚本，从 GitHub 拉取仓库并自动安装：

1. 下载一键安装脚本：
   ```bash
   wget -O install_human_thinking.sh https://raw.githubusercontent.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/main/install_from_github.sh
   ```

2. 赋予执行权限：
   ```bash
   chmod +x install_human_thinking.sh
   ```

3. 在 QwenPaw 根目录运行：
   ```bash
   ./install_human_thinking.sh
   ```

### 手动安装

1. 克隆本仓库：
   ```bash
   git clone https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager.git
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

### 自动安装

使用提供的安装脚本：

```bash
# 在 QwenPaw 根目录运行
bash src/qwenpaw/agents/tools/HumanThinkingMemoryManager/install.sh
```

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

### 记忆管理配置

可以在 `config.py` 中配置记忆管理参数：

```python
# 记忆管理配置
memory_manager = {
    "backend": "human_thinking",  # 使用 HumanThinkingMemoryManager
    "freeze_threshold_days": 30,  # 冷藏阈值（天）
    "defrost_relevance_threshold": 0.3,  # 解冻相关度阈值
    "max_memory_size": 10000,  # 最大记忆数量
    "compact_threshold": 1000  # 压缩阈值
}
```

## 使用方法

### 基本使用

1. **启用 HumanThinkingMemoryManager**：
   ```python
   # 在 config.py 中设置
   memory_manager.backend = "human_thinking"
   ```

2. **重启 QwenPaw 服务**：
   ```bash
   # 在 QwenPaw 根目录运行
   python -m qwenpaw
   ```

### 高级使用

#### 1. 存储记忆

```python
# 导入记忆管理器
from qwenpaw.agents.tools.HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager

# 初始化记忆管理器
memory_manager = HumanThinkingMemoryManager(
    working_dir="/path/to/agent/workspace",
    agent_id="agent_123"
)

# 启动记忆管理器
await memory_manager.start()

# 存储记忆
memory_id = await memory_manager.store_memory(
    content="这是一段重要的记忆内容",
    source_id="user",
    session_id="session_123",
    importance=5,  # 1-5，5最重要
    metadata={"entity_name": "张三", "entity_type": "person"}
)

# 关闭记忆管理器
await memory_manager.close()
```

#### 2. 搜索记忆

```python
# 搜索记忆
result = await memory_manager.memory_search(
    query="张三的信息",
    max_results=5,
    min_score=0.1
)

# 处理搜索结果
print(result.content[0].text)
```

#### 3. 记忆管理

```python
# 冷藏低频访问记忆
frozen_count = await memory_manager.freeze_memories()
print(f"已冷藏 {frozen_count} 条记忆")

# 解冻与查询相关的记忆
defrosted_count = await memory_manager.defrost_memories("张三")
print(f"已解冻 {defrosted_count} 条记忆")

# 获取记忆统计信息
stats = memory_manager.get_stats()
print("记忆统计:", stats)
```

#### 4. 记忆压缩

```python
# 压缩记忆
summary = await memory_manager.compact_memory(
    messages=messages,  # 消息列表
    previous_summary="",  # 之前的摘要
    extra_instruction="请总结这段对话的关键信息"
)

# 生成记忆摘要
summary = await memory_manager.summary_memory(
    messages=messages
)
```

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
├── install_from_github.sh  # 一键安装脚本
├── uninstall.sh       # 卸载脚本
└── README.md          # 文档
```

## 核心 API

### MemoryManager 类

#### 初始化

```python
HumanThinkingMemoryManager(working_dir: str, agent_id: str, config: Optional[dict] = None)
```

- `working_dir`：工作目录，用于存储记忆数据库
- `agent_id`：代理 ID，用于区分不同代理的记忆
- `config`：可选配置字典

#### 主要方法

- `start()`：启动记忆管理器
- `close()`：关闭记忆管理器
- `store_memory()`：存储新记忆
- `memory_search()`：搜索记忆
- `freeze_memories()`：冷藏低频访问记忆
- `defrost_memories()`：解冻与查询相关的记忆
- `get_stats()`：获取记忆统计信息
- `compact_memory()`：压缩记忆
- `summary_memory()`：生成记忆摘要

### 数据库操作

- `insert_memory()`：插入新记忆
- `get_memory()`：获取单个记忆
- `search_memories()`：搜索记忆
- `update_access_time()`：更新记忆访问时间
- `freeze_memory()`：冷藏记忆
- `defrost_memory()`：解冻记忆
- `get_stats()`：获取数据库统计信息

## 注意事项

1. **数据库备份**：在数据库结构升级时，系统会自动备份旧数据库，确保数据安全。

2. **性能优化**：对于大量记忆，建议配置外部嵌入模型以提高搜索性能。

3. **内存使用**：默认情况下，系统会自动管理内存使用，冷藏低频访问的记忆。

4. **兼容性**：HumanThinkingMemoryManager 与 QwenPaw 的默认 ReMeLightMemoryManager 完全兼容，可以随时切换。

5. **路径管理**：插件使用动态路径解析，确保无论放在什么位置都能正确工作。

## 故障排除

### 常见问题

1. **嵌入模型配置错误**
   - 症状：向量搜索不工作
   - 解决：检查嵌入模型配置和 API 密钥

2. **数据库权限问题**
   - 症状：无法创建或访问数据库
   - 解决：确保工作目录有写入权限

3. **内存使用过高**
   - 症状：系统内存使用过高
   - 解决：调整 `freeze_threshold_days` 参数，降低最大记忆数量

4. **搜索性能问题**
   - 症状：搜索速度慢
   - 解决：配置外部嵌入模型，调整搜索参数

### 日志

HumanThinkingMemoryManager 会生成详细的日志，位于 QwenPaw 的日志目录中。可以通过调整日志级别来控制日志输出：

```python
# 在 config.py 中设置
logging.level = "INFO"  # 可选：DEBUG, INFO, WARNING, ERROR
```

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
  - SQLite 本地存储
  - 记忆冷藏/解冻机制
  - 向量检索支持
  - 数据迁移功能
  - 版本管理

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

### 开发环境设置

1. 克隆仓库：
   ```bash
   git clone https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager.git
   ```

2. 安装依赖：
   ```bash
   # 依赖于 QwenPaw 的环境
   ```

3. 运行测试：
   ```bash
   # 运行测试脚本
   ```

## 许可证

MIT License

## 联系方式

- 项目地址：[https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager](https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager)
- 问题反馈：[https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/issues](https://github.com/kingsa2026/Q