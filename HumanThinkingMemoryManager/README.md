# HumanThinkingMemoryManager 文档

## 简介

HumanThinkingMemoryManager 是 QwenPaw 的一个高级记忆管理模块，提供类人记忆管理功能，包括：

- SQLite 本地存储（支持向量检索）
- 记忆冷藏/解冻机制
- 动态重要性标记
- 多模态检索
- 记忆固化与迁移

## 安装方法

### 1. 安装 Human Thinking Tool

将 `human_thinking_tool` 文件夹复制到 QwenPaw 的 `src/qwenpaw/agents/tools/` 目录下。

### 2. 运行安装脚本

在 `human_thinking_tool` 目录下运行安装脚本：

```bash
# Linux/Mac
chmod +x install.sh
./install.sh

# Windows
# 直接运行 install.sh 脚本
```

安装脚本会：
- 更新 `tools/__init__.py` 文件，添加 HumanThinkingTool 的导入
- 更新 `react_agent.py` 文件，添加 human_thinking 工具到工具列表
- 更新 `workspace.py` 文件，添加 HumanThinkingMemoryManager 作为可选的记忆管理后端
- 更新 `config.py` 文件，添加 human_thinking 工具的配置

## 配置方法

### 1. 启用 HumanThinkingMemoryManager

在 QwenPaw 的配置文件中设置：

```python
# config/config.py
memory_manager = MemoryManagerConfig(
    backend="human_thinking",  # 使用 HumanThinkingMemoryManager
    # 其他配置...
)
```

### 2. 配置嵌入模型

HumanThinkingMemoryManager 支持向量检索，需要配置嵌入模型：

```python
# config/config.py
embedding_config = EmbeddingConfig(
    backend="openai",  # 嵌入模型后端
    api_key="your_api_key",  # 嵌入模型 API 密钥
    base_url="https://api.openai.com/v1",  # 嵌入模型 API 基础 URL
    model_name="text-embedding-ada-002",  # 嵌入模型名称
    dimensions=1536,  # 嵌入维度
    # 其他配置...
)
```

### 3. 环境变量配置

也可以通过环境变量配置嵌入模型：

```bash
# Linux/Mac
export EMBEDDING_API_KEY="your_api_key"
export EMBEDDING_BASE_URL="https://api.openai.com/v1"
export EMBEDDING_MODEL_NAME="text-embedding-ada-002"

# Windows
set EMBEDDING_API_KEY=your_api_key
set EMBEDDING_BASE_URL=https://api.openai.com/v1
set EMBEDDING_MODEL_NAME=text-embedding-ada-002
```

## 使用方法

### 1. 基本使用

HumanThinkingMemoryManager 会自动集成到 QwenPaw 的工作流程中，无需手动调用。

### 2. 手动使用

```python
from qwenpaw.agents.tools.human_thinking_tool.core.memory_manager import HumanThinkingMemoryManager

# 初始化 HumanThinkingMemoryManager
memory_manager = HumanThinkingMemoryManager(
    working_dir="path/to/workspace",
    agent_id="agent_001"
)

# 启动内存管理器
await memory_manager.start()

# 存储记忆
memory_id = await memory_manager.store_memory(
    content="这是一段记忆内容",
    source_id="user",
    session_id="session_001",
    importance=3,  # 重要性等级 (1-5)
    metadata={"entity_name": "张三", "entity_type": "person"}
)

# 搜索记忆
search_result = await memory_manager.memory_search(
    query="张三",
    max_results=5,
    min_score=0.1
)

# 冷藏记忆
frozen_count = await memory_manager.freeze_memories()
print(f"冷藏了 {frozen_count} 个记忆")

# 解冻记忆
defrosted_count = await memory_manager.defrost_memories("张三")
print(f"解冻了 {defrosted_count} 个记忆")

# 获取记忆统计信息
stats = memory_manager.get_stats()
print(stats)

# 关闭内存管理器
await memory_manager.close()
```

## 功能特性

### 1. 记忆存储

- 支持存储文本记忆
- 支持设置记忆的重要性等级
- 支持存储记忆的元数据

### 2. 记忆检索

- 支持向量检索（基于嵌入模型）
- 支持关键词检索（作为向量检索的 fallback）
- 支持按重要性和时间排序

### 3. 记忆管理

- 记忆冷藏：自动识别和冷藏低频访问的记忆
- 记忆解冻：根据查询自动解冻相关的冷藏记忆
- 记忆重要性：动态调整记忆的重要性等级

### 4. 数据迁移

- 支持从旧格式（MEMORY.md, memory.json）迁移到新的 SQLite 格式

### 5. 版本管理

- 自动检查和升级数据库版本
- 确保数据结构的兼容性

## 示例代码

### 示例 1：基本使用

```python
# 初始化和使用 HumanThinkingMemoryManager
from qwenpaw.agents.tools.human_thinking_tool.core.memory_manager import HumanThinkingMemoryManager
import asyncio

async def main():
    # 初始化
    memory_manager = HumanThinkingMemoryManager(
        working_dir="./workspace",
        agent_id="test_agent"
    )
    
    # 启动
    await memory_manager.start()
    
    # 存储记忆
    await memory_manager.store_memory(
        content="今天天气很好，适合户外活动",
        source_id="user",
        importance=4
    )
    
    # 搜索记忆
    result = await memory_manager.memory_search(query="天气")
    print(result.content[0].text)
    
    # 关闭
    await memory_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 示例 2：高级使用

```python
# 高级使用示例
from qwenpaw.agents.tools.human_thinking_tool.core.memory_manager import HumanThinkingMemoryManager
import asyncio

async def main():
    # 初始化
    memory_manager = HumanThinkingMemoryManager(
        working_dir="./workspace",
        agent_id="advanced_agent",
        config={"vector_enabled": True}
    )
    
    # 启动
    await memory_manager.start()
    
    # 存储多条记忆
    memories = [
        ("张三是一名软件工程师", "user", 5, {"entity_name": "张三", "entity_type": "person"}),
        ("李四是一名产品经理", "user", 4, {"entity_name": "李四", "entity_type": "person"}),
        ("王五是一名设计师", "user", 3, {"entity_name": "王五", "entity_type": "person"}),
    ]
    
    for content, source_id, importance, metadata in memories:
        await memory_manager.store_memory(
            content=content,
            source_id=source_id,
            importance=importance,
            metadata=metadata
        )
    
    # 搜索相关记忆
    result = await memory_manager.memory_search(query="软件工程师")
    print("搜索结果:")
    print(result.content[0].text)
    
    # 冷藏记忆
    frozen = await memory_manager.freeze_memories()
    print(f"冷藏了 {frozen} 个记忆")
    
    # 解冻记忆
    defrosted = await memory_manager.defrost_memories("软件工程师")
    print(f"解冻了 {defrosted} 个记忆")
    
    # 获取统计信息
    stats = memory_manager.get_stats()
    print("统计信息:")
    print(stats)
    
    # 关闭
    await memory_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 常见问题

### 1. 向量检索不工作

**问题**：搜索结果为空或不相关

**解决方案**：
- 确保嵌入模型配置正确
- 检查 API 密钥是否有效
- 确保网络连接正常

### 2. 内存使用过高

**问题**：HumanThinkingMemoryManager 使用过多内存

**解决方案**：
- 减少存储的记忆数量
- 增加记忆冷藏的频率
- 调整重要性等级的计算逻辑

### 3. 数据库文件过大

**问题**：SQLite 数据库文件过大

**解决方案**：
- 定期执行 `compact_memory` 方法
- 清理不需要的记忆
- 考虑使用外部数据库

## 故障排除

### 1. 启动失败

**错误信息**：`Memory Manager not started`

**解决方案**：
- 检查工作目录权限
- 确保 SQLite 数据库文件可写
- 检查嵌入模型配置

### 2. 搜索失败

**错误信息**：`Search failed: [错误信息]`

**解决方案**：
- 检查嵌入模型连接
- 确保数据库已正确初始化
- 查看日志获取详细错误信息

### 3. 记忆存储失败

**错误信息**：`Memory Manager not started`

**解决方案**：
- 确保在存储记忆前已启动内存管理器
- 检查工作目录权限

## 性能优化

1. **启用向量检索**：向量检索比关键词检索更准确，但需要额外的计算资源
2. **调整重要性等级**：合理设置记忆的重要性等级，提高检索效率
3. **定期冷藏记忆**：自动冷藏低频访问的记忆，减少内存使用
4. **优化嵌入模型**：选择适合您需求的嵌入模型，平衡准确性和速度

## 版本历史

### v1.0.0
- 初始版本
- 支持基本的记忆存储和检索
- 支持记忆冷藏/解冻机制
- 支持向量检索

## 贡献

欢迎贡献代码和提出建议！请通过 GitHub 提交 Pull Request 或 Issue。

## 许可证

HumanThinkingMemoryManager 采用 MIT 许可证。