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

### 方式一：一键安装（推荐）

下载并运行一键安装脚本，自动完成所有安装步骤：

```bash
# 下载安装脚本
wget -O install_human_thinking.sh https://raw.githubusercontent.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/main/install.sh

# 赋予执行权限
chmod +x install_human_thinking.sh

# 在 QwenPaw 根目录运行（脚本会自动查找 QwenPaw 安装位置）
./install_human_thinking.sh
```

**脚本自动检测功能**：
- 自动查找 QwenPaw 根目录（支持 `~/.qwenpaw`、`~/.copaw` 等常见路径）
- 支持环境变量 `QWENPAW_ROOT` 和 `QWENPAW_WORKING_DIR`
- 支持命令行参数指定路径：`./install_human_thinking.sh /path/to/QwenPaw`

### 方式二：克隆仓库后安装

1. 克隆本仓库：
   ```bash
   git clone https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager.git
   ```

2. 将所有文件复制到 QwenPaw 的 `src/qwenpaw/agents/tools/HumanThinkingMemoryManager/` 目录下：
   ```bash
   mkdir -p /path/to/QwenPaw/src/qwenpaw/agents/tools/HumanThinkingMemoryManager
   cp -r QwenPaw_HumanThinkingMemoryManager/* /path/to/QwenPaw/src/qwenpaw/agents/tools/HumanThinkingMemoryManager/
   ```

3. 运行安装脚本：
   ```bash
   cd /path/to/QwenPaw/src/qwenpaw/agents/tools/HumanThinkingMemoryManager
   chmod +x install.sh
   ./install.sh
   ```

### 方式三：在 QwenPaw 源码目录安装

如果已经克隆了 QwenPaw 源码：

```bash
# 进入 QwenPaw 源码目录
cd /path/to/QwenPaw

# 克隆 HumanThinkingMemoryManager 到 tools 目录
git clone https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager.git src/qwenpaw/agents/tools/HumanThinkingMemoryManager

# 运行安装脚本
cd src/qwenpaw/agents/tools/HumanThinkingMemoryManager
chmod +x install.sh
./install.sh
```

## 从旧版本升级

如果您正在使用旧版本的 HumanThinkingMemoryManager，可以使用升级脚本一键升级到最新版本。

### 统一升级脚本（推荐）

升级脚本支持从**任意旧版本**自动升级到最新版本，包括：
- v1.0.0
- v1.0.1
- v1.0.2
- v1.0.2-beta0.1
- v1.0.2-beta0.2
- v1.0.2-beta0.3

升级脚本会自动：
1. 检测当前数据库版本
2. 备份数据库
3. 执行必要的数据库迁移
4. 更新代码
5. 安装到 QwenPaw

### Linux/Mac 系统

```bash
cd /path/to/QwenPaw/src/qwenpaw/agents/tools/HumanThinkingMemoryManager
./upgrade.sh
```

### Windows 系统

```bash
cd C:\path\to\QwenPaw\src\qwenpaw\agents\tools\HumanThinkingMemoryManager
upgrade.bat
```

### 单独升级数据库

如果只需要升级数据库（不更新代码），可以使用 Python 脚本：

```bash
python upgrade.py --db-path /path/to/database.db --backup-dir ./backups
```

## 配置选项

### 嵌入配置

HumanThinkingMemoryManager 支持使用外部嵌入模型进行向量检索。可以在 `config.py` 中配置：

```python
# 嵌入配置
embedding_config = {
    "backend": "openai",  # 支持 openai, azure, ollama 等
    "model": "text-embedding-ada-002",
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1"  # 可选，自定义 API 地址
}
```

### 环境变量

HumanThinkingMemoryManager 支持以下环境变量：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `QWENPAW_WORKING_DIR` | QwenPaw 工作目录 | `~/.qwenpaw` |
| `QWENPAW_ROOT` | QwenPaw 源码根目录 | 自动检测 |
| `HTMM_DB_PATH` | 数据库路径 | `{WORKING_DIR}/memory/human_thinking.db` |

## 快速验证

安装完成后，可以运行快速验证脚本检查功能是否正常：

```bash
cd /path/to/QwenPaw/src/qwenpaw/agents/tools/HumanThinkingMemoryManager
python quick_verify.py
```

## 使用方法

### 在 QwenPaw 中启用

1. 在 QwenPaw 配置文件中设置：
   ```python
   memory_manager_backend = "human_thinking"
   ```

2. 或者在 UI 中选择 `human_thinking` 作为记忆后端

3. 重启 QwenPaw 服务以应用更改

### API 使用

```python
from core.memory_manager import HumanThinkingMemoryManager

# 初始化
manager = HumanThinkingMemoryManager(
    working_dir="./workspace",
    agent_id="my_agent"
)

# 存储记忆
await manager.store_memory(
    content="这是一个重要的记忆",
    importance=5,
    session_id="session_123"
)

# 搜索记忆
results = await manager.search_by_text("重要", max_results=5)

# 获取统计信息
stats = await manager.get_stats()
```

## 版本历史

### v1.0.2-beta0.3：存储优化与搜索性能版本（最新）

**核心亮点**：
- **压缩存储**：实现记忆内容的压缩存储，减少磁盘占用
- **索引优化**：优化数据库索引结构，添加复合索引和搜索优化索引
- **热数据/冷数据分层存储**：实现热数据/冷数据分层存储，提高频繁访问数据的读取速度
- **HNSW-like向量搜索算法**：集成更先进的HNSW-like向量搜索算法，提高搜索效率
- **增量索引**：实现增量索引更新，避免全量重建，提高索引更新性能

### v1.0.2-beta0.2：智能记忆管理版本

**核心亮点**：
- **智能记忆管理**：实现记忆分类、记忆关联、记忆摘要、记忆优先级调整
- **会话管理**：实现了SessionManager类，支持会话的创建、更新和超时清理
- **并发安全**：添加了线程安全的缓存操作，使用RLock确保并发安全
- **会话隔离**：确保不同agent的会话不会混淆，每个agent有独立的缓存池

### v1.0.2-beta0.1：重构版本

**核心亮点**：
- **项目结构优化**：重构项目结构，将文件从HumanThinkingMemoryManager目录移到根目录
- **bug修复**：修复版本管理表名问题、数据库索引问题和配置属性名问题

### v1.0.4：缓存优化版本

### v1.0.3：性能优化版本

### v1.0.2：集成版本

### v1.0.1：搜索优化版本

### v1.0.0：初始版本

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
