# Human Thinking Memory Manager

> QwenPaw 超级神经记忆系统 - 跨Session碎片化记忆整合 + 神经元感知向量记忆检索架构

## 版本兼容性

✅ **已适配 QwenPaw 最新版本 v1.1.2b2**

本模块已完整适配 QwenPaw v1.1.2b2 版本，包括：
- 扩展 `memory_manager_backend: Literal["remelight", "human_thinking"]` 配置
- 用户可在 config.json 或 workspace/agent.json 中自行选择使用哪个记忆管理器
- 完整实现 BaseMemoryManager 抽象接口
- 支持向后兼容旧版本 QwenPaw（v1.1.2b1 及更早版本）

### 如何选择使用 HumanThinkingMemoryManager

安装完成后，在以下配置文件中设置即可：

**方式一：在根配置 config.json 中设置（全局生效）**
```json
{
  "agents": {
    "running": {
      "memory_manager_backend": "human_thinking"
    }
  }
}
```

**方式二：在 workspace/agent.json 中设置（仅对特定 agent 生效）**
```json
{
  "running": {
    "memory_manager_backend": "human_thinking"
  }
}
```

默认值为 `"remelight"`，使用 QwenPaw 自带的记忆管理器。

## 快速开始

### 一键安装（最简单）

直接调用仓库脚本，无需下载（推荐）：

```bash
bash <(curl -s https://raw.githubusercontent.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/main/install.sh)
```

或者使用 wget：

```bash
wget -qO- https://raw.githubusercontent.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/main/install.sh | bash
```

### 方式二：先下载再运行

下载安装脚本并运行：

```bash
wget -O install_human_thinking.sh https://raw.githubusercontent.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/main/install.sh
chmod +x install_human_thinking.sh
./install_human_thinking.sh
```

**脚本自动检测功能**：
- ✅ 自动查找 QwenPaw 安装位置（支持 `~/.qwenpaw`、`~/.copaw` 等）
- ✅ 支持环境变量 `QWENPAW_ROOT` 和 `QWENPAW_WORKING_DIR`
- ✅ 支持命令行指定路径：`./install_human_thinking.sh /path/to/QwenPaw`

---

## 功能特性

### 🧠 核心记忆功能

#### 1. SQLite 本地存储架构
- **零依赖**：内置 SQLite，无需外部数据库服务
- **本地存储**：数据完全存储在本地，保证隐私安全
- **类人记忆模型**：模拟人类记忆的存储和检索机制
- **高效存储**：优化的数据库结构，支持快速存取大量记忆
- **自动管理**：自动处理记忆的创建、更新和删除

#### 2. 模拟人类记忆检索机制
- **语义搜索**：使用向量嵌入技术实现语义理解
- **关联检索**：基于记忆之间的关联关系进行检索
- **重要性排序**：根据记忆重要性和访问频率排序
- **上下文感知**：考虑当前上下文进行检索
- **模糊匹配**：支持部分匹配和近似匹配

#### 3. 跨 Session 记忆管理
- **持久化存储**：记忆在会话之间持久化存储
- **会话关联**：自动关联不同会话中的相关记忆
- **跨会话检索**：新会话可检索之前会话的记忆
- **记忆整合**：自动整合跨会话的相关记忆

### 🔥 存储优化功能

#### 4. 记忆冷藏/解冻机制
- **自动冷藏**：低频访问的记忆自动冷藏，优化存储
- **手动冷藏**：支持手动标记记忆为冷藏状态
- **解冻机制**：需要时自动解冻相关记忆
- **状态管理**：清晰的冷藏/解冻状态管理

#### 5. 热数据/冷数据分层存储
- **记忆温度概念**：综合考虑访问频率、重要性、时间衰减
- **固定记忆机制**：保护重要记忆不被自动降级
- **自动分层**：基于记忆温度自动分层存储
- **性能优化**：热数据快速访问，冷数据压缩存储

#### 6. 压缩存储与索引优化
- **压缩存储**：使用 zlib 压缩 + Base64 编码，减少磁盘占用
- **复合索引**：优化的数据库索引结构，提高查询速度
- **搜索优化索引**：专门为搜索场景优化的索引
- **增量索引**：新记忆添加时无需全量重建索引

### ⚡ 搜索性能优化

#### 7. HNSW-like 向量搜索算法
- **分层索引**：基于分层的类 HNSW 算法
- **高效搜索**：对数级别的搜索复杂度
- **高召回率**：保持高精度的同时提高召回率
- **可调参数**：支持调整搜索精度和性能

#### 8. 混合检索机制
- **向量 + 文本**：结合向量检索和文本检索
- **权重调整**：基于搜索频率自动调整权重
- **相关性排序**：综合考虑相关性和重要性

### 🎯 智能记忆管理

#### 9. 记忆分类与标签
- **自动分类**：自动对记忆进行分类
- **多标签支持**：一个记忆可关联多个标签
- **分类管理**：创建、查询、按分类筛选记忆

#### 10. 记忆关联系统
- **自动关联**：自动建立记忆之间的关联关系
- **关联类型**：支持不同类型的关联关系
- **相似度评分**：为关联关系设置相似度评分
- **相关记忆查询**：查询与指定记忆相关的其他记忆

#### 11. 记忆优先级调整
- **重要性等级**：1-5 级重要性标记
- **自动调整**：基于访问频率和搜索频率自动调整
- **优先级队列**：按优先级排序返回结果

### 💬 平台集成

#### 12. 飞书消息处理
- **回复链处理**：支持飞书回复链消息解析
- **@提及处理**：自动提取和处理@提及信息
- **引用消息**：支持引用内容的解析和存储
- **重要消息识别**：自动识别重要消息并提升优先级

#### 13. 跨 Session 记忆搜索
- **跨 Session 搜索**：可选择搜索所有会话的记忆
- **Session 来源标记**：清晰标记记忆所属会话
- **相关历史记忆推送**：新 Session 时主动推送相关历史记忆

### 🛠️ 开发功能

#### 14. 版本管理与迁移
- **自动版本检测**：启动时自动检测数据库版本
- **渐进式升级**：支持从任意旧版本升级
- **自动备份**：升级前自动备份数据库
- **升级记录**：记录所有升级历史

#### 15. 调试与测试
- **快速验证脚本**：`quick_verify.py` 快速检查功能
- **完整测试套件**：全面的单元测试
- **会话管理测试**：验证会话隔离和缓存机制
- **智能记忆测试**：验证分类、关联、优先级功能

---

## 安装方法

### 方式一：直接调用仓库脚本（最简单）

```bash
# 方式 A：使用 curl（推荐）
bash <(curl -s https://raw.githubusercontent.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/main/install.sh)

# 方式 B：使用 wget
wget -qO- https://raw.githubusercontent.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/main/install.sh | bash
```

### 方式二：先下载再运行

```bash
# 下载安装脚本
wget -O install_human_thinking.sh https://raw.githubusercontent.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager/main/install.sh

# 赋予执行权限
chmod +x install_human_thinking.sh

# 运行安装脚本（会自动查找 QwenPaw）
./install_human_thinking.sh
```

**自动检测路径**：
- 当前目录
- 脚本目录向上 5 层
- 环境变量：`QWENPAW_ROOT`、`QWENPAW_WORKING_DIR`
- 常见位置：`~/.qwenpaw`、`~/.copaw`、`~/QwenPaw`、`/opt/QwenPaw`

### 方式二：克隆仓库安装

```bash
# 克隆仓库
git clone https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager.git

# 复制到 QwenPaw tools 目录
cp -r QwenPaw_HumanThinkingMemoryManager /path/to/QwenPaw/src/qwenpaw/agents/tools/

# 运行安装脚本
cd /path/to/QwenPaw/src/qwenpaw/agents/tools/HumanThinkingMemoryManager
chmod +x install.sh
./install.sh
```

### 方式三：在 QwenPaw 源码目录安装

```bash
cd /path/to/QwenPaw
git clone https://github.com/kingsa2026/QwenPaw_HumanThinkingMemoryManager.git \
  src/qwenpaw/agents/tools/HumanThinkingMemoryManager
cd src/qwenpaw/agents/tools/HumanThinkingMemoryManager
chmod +x install.sh
./install.sh
```

---

## 升级指南

### 自动升级（推荐）

```bash
# 一键升级（支持从任意旧版本升级）
./upgrade.sh
```

**升级脚本自动完成**：
1. ✅ 检测当前数据库版本
2. ✅ 备份数据库
3. ✅ 执行必要的数据库迁移
4. ✅ 更新代码
5. ✅ 安装到 QwenPaw

**支持的版本**：v1.0.0 ~ v1.0.2-beta0.3

### 单独升级数据库

```bash
python upgrade.py --db-path /path/to/database.db --backup-dir ./backups
```

---

## 配置选项

### 启用 HumanThinkingMemoryManager

在 QwenPaw 配置文件中设置：

```python
memory_manager_backend = "human_thinking"
```

或在 UI 中选择 `human_thinking` 作为记忆后端。

### 环境变量

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `QWENPAW_WORKING_DIR` | QwenPaw 工作目录 | `~/.qwenpaw` |
| `QWENPAW_ROOT` | QwenPaw 源码根目录 | 自动检测 |
| `HTMM_DB_PATH` | 数据库路径 | `{WORKING_DIR}/memory/human_thinking.db` |

### 嵌入配置

在 `config.py` 中配置向量嵌入模型：

```python
embedding_config = {
    "backend": "openai",  # openai, azure, ollama
    "model": "text-embedding-ada-002",
    "api_key": "your-api-key",
    "base_url": "https://api.openai.com/v1"
}
```

---

## API 使用

### Python API

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

# 跨 Session 搜索
results = await manager.search_by_text(
    "重要",
    cross_session=True,  # 搜索所有 Session
    max_results=10
)

# 获取统计信息
stats = await manager.get_stats()

# 冷藏记忆
await manager.freeze_memories([memory_id])

# 解冻记忆
await manager.defrost_memories([memory_id])
```

### 记忆分类与关联

```python
# 创建分类
await manager.create_category("工作", "工作相关的记忆")
await manager.create_category("学习", "学习相关的记忆")

# 添加分类
await manager.add_category_to_memory(memory_id, "工作")

# 关联记忆
await manager.link_memories(memory_id1, memory_id2, "related")

# 获取相关记忆
related = await manager.get_related_memories(memory_id)
```

---

## 快速验证

快速验证功能：

```bash
python quick_verify.py
```

运行完整测试：

```bash
python test_human_thinking_memory_manager.py
```

会话管理测试：

```bash
python test_session_management.py
```

智能记忆测试：

```bash
python test_intelligent_memory.py
```

---

## 版本历史

### v1.0.2-beta0.3（最新）
- 压缩存储减少磁盘占用
- HNSW-like 向量搜索算法
- 热数据/冷数据分层存储
- 固定记忆机制
- 增量索引更新

### v1.0.2-beta0.2
- 智能记忆管理
- 会话管理增强
- 并发安全优化

### v1.0.2-beta0.1
- 项目结构重构
- bug 修复

---

## 目录结构

```
HumanThinkingMemoryManager/
├── core/                    # 核心模块
│   ├── memory_manager.py   # 记忆管理器
│   └── database.py         # 数据库操作
├── search/                  # 搜索模块
│   └── vector.py           # 向量搜索
├── hooks/                   # 钩子模块
│   ├── memory_hooks.py     # 记忆钩子
│   └── feishu_message_parser.py  # 飞书消息解析
├── utils/                   # 工具模块
│   └── version.py          # 版本管理
├── config/                  # 配置模块
│   └── config.py           # 配置管理
├── install.sh              # 安装脚本
├── uninstall.sh            # 卸载脚本
├── upgrade.sh              # 升级脚本
├── upgrade.py              # Python 升级脚本
├── quick_verify.py         # 快速验证
├── test_*.py               # 测试脚本
└── README.md               # 文档
```

---

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
