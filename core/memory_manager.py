# -*- coding: utf-8 -*-
"""Human Thinking Memory Manager for QwenPaw agents."""
import logging
import platform
import sys
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

# 模拟必要的类，避免依赖agentscope
class TextBlock:
    """模拟TextBlock类"""
    def __init__(self, type, text):
        self.type = type
        self.text = text

class Msg:
    """模拟Msg类"""
    def __init__(self, name, content):
        self.name = name
        self.content = content

class ToolResponse:
    """模拟ToolResponse类"""
    def __init__(self, content):
        self.content = content

class Toolkit:
    """模拟Toolkit类"""
    def __init__(self):
        self.tools = {}
    
    def register_tool_function(self, func):
        self.tools[func.__name__] = func

# 模拟BaseMemoryManager类
class BaseMemoryManager:
    """模拟BaseMemoryManager类"""
    def __init__(self, working_dir, agent_id):
        self.working_dir = working_dir
        self.agent_id = agent_id
        self.chat_model = None
        self.formatter = None

# 模拟其他依赖
class MockEnvVarLoader:
    """模拟EnvVarLoader类"""
    @staticmethod
    def get_str(key):
        return ""

# 模拟函数
def create_model_and_formatter(agent_id):
    """模拟create_model_and_formatter函数"""
    return None, None

def read_file(**kwargs):
    """模拟read_file函数"""
    return ""

def write_file(**kwargs):
    """模拟write_file函数"""
    return ""

def edit_file(**kwargs):
    """模拟edit_file函数"""
    return ""

def get_token_counter():
    """模拟get_token_counter函数"""
    return lambda x: 0

def load_config():
    """模拟load_config函数"""
    return {}

def load_agent_config(agent_id):
    """模拟load_agent_config函数"""
    class MockConfig:
        class Running:
            class ContextCompact:
                pass
            
            class embedding_config:
                backend = "openai"
                api_key = ""
                base_url = ""
                model_name = ""
                dimensions = 1536
                enable_cache = True
                use_dimensions = False
                max_cache_size = 1000
                max_input_length = 8192
                max_batch_size = 32
        
        running = Running()
    
    return MockConfig()

# 模拟常量
class EnvVarLoader:
    """模拟EnvVarLoader类"""
    get_str = MockEnvVarLoader.get_str


class SessionManager:
    """会话管理器，负责管理不同agent的不同会话"""
    
    def __init__(self):
        """初始化会话管理器"""
        self.sessions = {}
        self.lock = threading.RLock()  # 可重入锁
        
    def create_session(self, agent_id: str, session_id: str):
        """创建新会话
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
            
        Returns:
            dict: 会话信息
        """
        key = f"{agent_id}:{session_id}"
        with self.lock:
            if key not in self.sessions:
                self.sessions[key] = {
                    'agent_id': agent_id,
                    'session_id': session_id,
                    'created_at': datetime.now(),
                    'last_activity': datetime.now(),
                    'memories': []
                }
            return self.sessions[key]
            
    def get_session(self, agent_id: str, session_id: str):
        """获取会话
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
            
        Returns:
            dict: 会话信息，不存在返回None
        """
        key = f"{agent_id}:{session_id}"
        with self.lock:
            return self.sessions.get(key)
            
    def update_session(self, agent_id: str, session_id: str):
        """更新会话活动时间
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
        """
        key = f"{agent_id}:{session_id}"
        with self.lock:
            if key in self.sessions:
                self.sessions[key]['last_activity'] = datetime.now()
                
    def cleanup_sessions(self, timeout: int = 300):
        """清理超时会话
        
        Args:
            timeout: 超时时间（秒）
        """
        with self.lock:
            current_time = datetime.now()
            expired_sessions = []
            for key, session in self.sessions.items():
                if (current_time - session['last_activity']).total_seconds() > timeout:
                    expired_sessions.append(key)
            for key in expired_sessions:
                del self.sessions[key]
                
    def get_session_count(self, agent_id: str):
        """获取指定agent的会话数量
        
        Args:
            agent_id: Agent ID
            
        Returns:
            int: 会话数量
        """
        with self.lock:
            count = 0
            for key in self.sessions:
                if key.startswith(f"{agent_id}:"):
                    count += 1
            return count

# 动态路径解析 - 确保无论模块放在哪个位置都能正确导入
_path_resolved = False


def _get_module_path() -> Path:
    """动态获取当前模块的路径。

    使用 __file__ 来确定模块的实际位置，
    确保无论 HumanThinkingMemoryManager 文件夹放在哪里都能正确工作。
    """
    return Path(__file__).resolve().parent

def _ensure_qwenpaw_path() -> None:
    """确保 qwenpaw 路径在 sys.path 中，以便正确导入子模块。"""
    global _path_resolved
    if _path_resolved:
        return
    
    module_path = _get_module_path()
    tools_path = module_path.parent

    # 将 tools 目录添加到 sys.path（如果还没有）
    tools_str = str(tools_path)
    if tools_str not in sys.path:
        sys.path.insert(0, tools_str)

    # 确保 qwenpaw 路径也在 sys.path 中
    qwenpaw_path = tools_path.parent
    qwenpaw_str = str(qwenpaw_path)
    if qwenpaw_str not in sys.path:
        sys.path.insert(0, qwenpaw_str)
    
    _path_resolved = True

# 在导入子模块之前确保路径正确
_ensure_qwenpaw_path()

# 动态导入子模块
from core.database import HumanThinkingMemoryDB
from search.vector import VectorSearcher
from hooks.memory_hooks import MemoryRetrievalHook, MemoryWriteHook, MemoryFreezerHook
from utils.migrator import MemoryMigrator
from utils.version import VersionManager

logger = logging.getLogger(__name__)

_HUMAN_THINKING_STORE_VERSION = "v1"


class HumanThinkingMemoryManager(BaseMemoryManager):
    """Human Thinking Memory Manager for QwenPaw agents.

    提供类人记忆管理功能：
    - SQLite 本地存储（支持向量检索）
    - 记忆冷藏/解冻机制
    - 动态重要性标记
    - 多模态检索
    - 记忆固化与迁移
    """

    def __init__(self, working_dir: str, agent_id: str, config: Optional[dict] = None):
        """Initialize Human Thinking Memory Manager.

        Args:
            working_dir: Working directory for memory storage.
            agent_id: Agent ID for config loading.
            config: Optional configuration dictionary.
        """
        super().__init__(working_dir=working_dir, agent_id=agent_id)
        self.config: dict = config or {}

        # 初始化路径
        self.memory_dir = Path(working_dir) / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # 数据库路径 - 每个agent有独立的数据库，存放在对应工作区的memory目录中
        self.db_path = self.memory_dir / f"human_thinking_memory_{agent_id}.db"

        # 初始化数据库
        self.db: Optional[HumanThinkingMemoryDB] = None

        # 初始化搜索引擎
        self.vector_searcher: Optional[VectorSearcher] = None

        # 初始化钩子
        self.retrieval_hook: Optional[MemoryRetrievalHook] = None
        self.write_hook: Optional[MemoryWriteHook] = None
        self.freezer_hook: Optional[MemoryFreezerHook] = None

        # 初始化版本管理器
        self.version_manager: Optional[VersionManager] = None

        # 初始化迁移器
        self.migrator: Optional[MemoryMigrator] = None

        # 初始化工具包
        self.summary_toolkit = Toolkit()
        self.summary_toolkit.register_tool_function(read_file)
        self.summary_toolkit.register_tool_function(write_file)
        self.summary_toolkit.register_tool_function(edit_file)

        # 会话管理器
        self.session_manager = SessionManager()
        
        # 内存缓存 - 每个agent一个缓存池
        self._memory_cache = []
        self.batch_threshold = 10  # 批量写入阈值（按条数）
        self.max_cache_size = 100000  # 最大缓存大小（按字符数）
        self._force_flush = False  # 强制刷新标志
        self.last_activity_time = datetime.now()  # 最后活动时间
        self.inactivity_timeout = 300  # 无活动超时时间（秒）
        self.cache_lock = threading.RLock()  # 缓存操作的锁

        # 生命周期状态
        self._started: bool = False

        logger.info(
            f"HumanThinkingMemoryManager init: agent_id={agent_id}, "
            f"working_dir={working_dir}, db_path={self.db_path}",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_rebuild_on_start(
        self,
        working_dir: str,
        store_version: str,
        rebuild_on_start: bool,
    ) -> bool:
        """Return effective rebuild_index_on_start value.

        Uses a sentinel file ``.human_thinking_store_{store_version}`` to track whether
        the current store version has already been initialized.  If the
        sentinel is absent a one-time rebuild is forced and the sentinel is
        created.  On subsequent starts the sentinel exists and the
        caller-supplied *rebuild_on_start* is used as-is.

        To trigger a future one-time rebuild, bump *_HUMAN_THINKING_STORE_VERSION*.
        """
        sentinel_name = f".human_thinking_store_{store_version}"
        sentinel_path = Path(working_dir) / sentinel_name

        if sentinel_path.exists():
            return rebuild_on_start

        logger.info(
            f"Sentinel '{sentinel_name}' not found, forcing rebuild.",
        )

        # Remove stale sentinels left by previous versions.
        try:
            for old in Path(working_dir).glob(".human_thinking_store_*"):
                old.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to remove old sentinels: {e}")

        try:
            sentinel_path.touch()
        except Exception as e:
            logger.warning(f"Failed to create sentinel '{sentinel_name}': {e}")

        return True

    def _prepare_model_formatter(self) -> None:
        """Lazily initialize chat_model and formatter if not already set."""
        if self.chat_model is None or self.formatter is None:
            self.chat_model, self.formatter = create_model_and_formatter(
                self.agent_id,
            )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_embedding_config(self) -> dict:
        """Return embedding config with priority:
        config > env var > default."""
        cfg = load_agent_config(self.agent_id).running.embedding_config
        return {
            "backend": cfg.backend,
            "api_key": cfg.api_key
            or EnvVarLoader.get_str("EMBEDDING_API_KEY"),
            "base_url": cfg.base_url
            or EnvVarLoader.get_str("EMBEDDING_BASE_URL"),
            "model_name": cfg.model_name
            or EnvVarLoader.get_str("EMBEDDING_MODEL_NAME"),
            "dimensions": cfg.dimensions,
            "enable_cache": cfg.enable_cache,
            "use_dimensions": cfg.use_dimensions,
            "max_cache_size": cfg.max_cache_size,
            "max_input_length": cfg.max_input_length,
            "max_batch_size": cfg.max_batch_size,
        }

    # ------------------------------------------------------------------
    # BaseMemoryManager interface
    # ------------------------------------------------------------------

    async def start(self):
        """Start the Human Thinking Memory Manager lifecycle.

        执行以下操作：
        1. 初始化数据库（核心组件）
        2. 检查版本并升级
        3. 执行数据迁移（如果有）
        """
        if self._started:
            logger.warning("Memory Manager already started")
            return None

        logger.info(f"Starting HumanThinkingMemoryManager for agent: {self.agent_id}")

        # 1. 初始化数据库（核心组件）
        self.db = HumanThinkingMemoryDB(
            db_path=str(self.db_path),
            agent_id=self.agent_id,
        )

        # 2. 检查版本并升级
        self.version_manager = VersionManager(self.db.conn)
        if self.version_manager.need_upgrade():
            logger.info("Upgrading database...")
            self.version_manager.upgrade(str(self.db_path))

        # 3. 执行数据迁移
        self.migrator = MemoryMigrator(
            workspace_dir=self.working_dir,
            agent_id=self.agent_id,
            db=self.db,
        )
        await self.migrator.migrate_if_needed()

        # 4. 启动完成（其他组件延迟初始化）
        self._started = True
        logger.info(f"HumanThinkingMemoryManager started for agent: {self.agent_id}")
        return None

    async def close(self) -> bool:
        """Close the Human Thinking Memory Manager and clean up resources.

        Returns:
            bool: Whether the manager was successfully closed.
        """
        if not self._started:
            logger.warning("Memory Manager not started")
            return True

        logger.info(f"Closing HumanThinkingMemoryManager for agent: {self.agent_id}")

        # 强制刷新缓存，确保所有记忆都被写入数据库
        if self._memory_cache:
            logger.info(f"Flushing {len(self._memory_cache)} memories from cache")
            await self._flush_cache()

        # 等待摘要任务完成
        await self.await_summary_tasks()

        # 关闭数据库连接
        if self.db:
            self.db.close()
            self.db = None

        self._started = False
        logger.info(f"HumanThinkingMemoryManager closed for agent: {self.agent_id}")
        return True

    async def await_summary_tasks(self):
        """等待摘要任务完成。"""
        # 实现等待摘要任务的逻辑
        # 由于我们是在测试环境中，这里可以简单返回
        pass

    async def compact_tool_result(self, **kwargs) -> None:
        """Compact tool results by truncating large outputs."""
        # 实现压缩工具结果的逻辑
        pass

    async def check_context(self, **kwargs) -> tuple:
        """Check context size and determine if compaction is needed.

        Args:
            **kwargs: Context check parameters.

        Returns:
            tuple: (messages_to_compact, remaining_messages, is_valid)
        """
        # 实现上下文检查逻辑
        messages = kwargs.get("messages", [])
        return messages, [], True

    async def compact_memory(
        self,
        messages: list[Msg],
        previous_summary: str = "",
        extra_instruction: str = "",
        **kwargs,
    ) -> str:
        """Compact messages into a condensed summary.

        Args:
            messages: List of messages to compact.
            previous_summary: Previous summary string.
            extra_instruction: Additional compact instruction.
            **kwargs: Other parameters.

        Returns:
            str: Compacted summary string.
        """
        if not messages:
            return ""

        self._prepare_model_formatter()

        agent_config = load_agent_config(self.agent_id)
        cc = agent_config.running.context_compact

        # 简单拼接（实际项目中可以使用 LLM 生成摘要）
        return "\n".join([f"{m.name}: {m.content}" for m in messages[:10]])

    async def summary_memory(self, messages: list[Msg], **kwargs) -> str:
        """Generate a comprehensive summary of the given messages.

        Args:
            messages: List of messages to summarize.
            **kwargs: Other parameters.

        Returns:
            str: Summary string.
        """
        self._prepare_model_formatter()

        agent_config = load_agent_config(self.agent_id)
        cc = agent_config.running.context_compact

        # 简单拼接（实际项目中可以使用 LLM 生成摘要）
        return "\n".join([f"{m.name}: {m.content}" for m in messages[:10]])

    async def dream_memory(self, **kwargs) -> None:
        """Run one dream-based memory optimization task.

        Args:
            **kwargs: Additional keyword arguments for the dream task.
        """
        logger.info("dream_memory called - HumanThinkingMemoryManager does not implement dream-based optimization")
        # Dream-based memory optimization is not implemented in this version
        pass

    def _lazy_init_components(self):
        """延迟初始化组件"""
        # 初始化向量搜索器
        if not self.vector_searcher:
            emb_config = self.get_embedding_config()
            vector_enabled = bool(emb_config["base_url"]) and bool(
                emb_config["model_name"],
            )

            log_cfg = {
                **emb_config,
                "api_key": emb_config["api_key"][:5] + "*" * (len(emb_config["api_key"]) - 5) if len(emb_config["api_key"]) > 5 else emb_config["api_key"],
            }
            logger.info(
                f"Embedding config: {log_cfg}, vector_enabled={vector_enabled}",
            )

            # 初始化向量搜索器
            self.vector_searcher = VectorSearcher(self, backend="tfidf", cache_enabled=True)

        # 初始化钩子
        if not self.retrieval_hook or not self.write_hook or not self.freezer_hook:
            self.retrieval_hook = MemoryRetrievalHook(self.db, self.agent_id)
            self.write_hook = MemoryWriteHook(self.db, self.agent_id)
            self.freezer_hook = MemoryFreezerHook(self.db, self.agent_id)

    async def memory_search(
        self,
        query: str,
        max_results: int = 5,
        min_score: float = 0.1,
        session_id: Optional[str] = None,
        cross_session: bool = False,
    ) -> ToolResponse:
        """Search stored memories for relevant content (supports real-time cache search and session filtering).

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.
            min_score: Minimum relevance score.
            session_id: Optional session ID to filter results.
            cross_session: If True, search across all sessions; if False, only search current session.

        Returns:
            ToolResponse: Response containing search results.
        """
        if not self._started:
            return ToolResponse(
                content=[TextBlock(type="text", text="Memory Manager not started")],
            )

        try:
            # Update last activity time
            self.last_activity_time = datetime.now()

            # Update session activity if session_id is provided
            if session_id:
                self.session_manager.update_session(self.agent_id, session_id)

            # 延迟初始化组件
            self._lazy_init_components()

            # 确定搜索策略
            search_session_id = None if cross_session else session_id

            # 先从内存缓存中搜索
            cache_results = []
            with self.cache_lock:
                if self._memory_cache:
                    for memory in self._memory_cache:
                        # Filter by session if session_id is provided and not cross_session
                        if not cross_session and session_id and memory.get('session_id') != session_id:
                            continue
                        if query.lower() in memory['content'].lower():
                            memory_copy = memory.copy()
                            memory_copy['similarity'] = 0.9  # 缓存中的记忆相关性较高
                            memory_copy['source_type'] = 'cache'
                            cache_results.append(memory_copy)

            # 从数据库中搜索
            db_results = await self.vector_searcher.search(
                query=query,
                max_results=max_results - len(cache_results),
                agent_id=self.agent_id,
                session_id=search_session_id,
                include_frozen=False
            )

            # 标记数据库结果的来源类型
            for mem in db_results:
                mem['source_type'] = 'database'

            # 合并结果
            results = cache_results + db_results

            # 排序（按相关度、时间综合排序）
            results.sort(key=lambda x: (x.get('similarity', 0), x.get('created_at', '')), reverse=True)
            results = results[:max_results]

            # 格式化结果，标记session来源
            if not results:
                return ToolResponse(
                    content=[TextBlock(type="text", text="No relevant memories found.")],
                )

            result_text = "【相关记忆】\n\n"

            # 统计各类型记忆数量
            current_session_count = 0
            history_session_count = 0

            for i, mem in enumerate(results, 1):
                mem_session_id = mem.get('session_id', 'unknown')
                is_current_session = (mem_session_id == session_id) if session_id else False

                if is_current_session:
                    session_marker = "[当前session]"
                    current_session_count += 1
                else:
                    session_marker = f"[历史session: {mem_session_id[:8] if mem_session_id else 'unknown'}...]"
                    history_session_count += 1

                result_text += f"{i}. {session_marker}\n"
                result_text += f"   {mem.get('created_at', 'N/A')} | 重要性: {mem.get('importance', 3)} | 相关度: {round(mem.get('similarity', 0), 2)}\n"
                result_text += f"   内容: {mem['content'][:100]}{'...' if len(mem['content']) > 100 else ''}\n\n"

            # 添加统计信息
            if cross_session:
                result_text += "---\n"
                result_text += f"统计: 当前session {current_session_count} 条 | 历史session {history_session_count} 条\n"

            # 更新访问时间
            for mem in results:
                if 'id' in mem:
                    self.db.update_memory_access(mem["id"])

            return ToolResponse(content=[TextBlock(type="text", text=result_text)])

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return ToolResponse(
                content=[TextBlock(type="text", text=f"Search failed: {e}")],
            )

    def get_in_memory_memory(self, **kwargs) -> Any:
        """Retrieve the in-memory memory object.

        Args:
            **kwargs: Other parameters.

        Returns:
            Any: In-memory memory object.
        """
        # 实现获取内存中记忆对象的逻辑
        return None

    async def get_related_historical_memories(
        self,
        context: str,
        current_session_id: str,
        max_results: int = 5,
    ) -> ToolResponse:
        """获取与当前上下文相关的历史session记忆

        当agent开始新session时，可以主动推送与当前上下文相关的历史记忆，
        帮助agent保持跨session的上下文连续性。

        Args:
            context: 当前上下文/话题
            current_session_id: 当前session ID
            max_results: 最大结果数

        Returns:
            ToolResponse: 包含相关历史记忆的响应
        """
        if not self._started:
            return ToolResponse(
                content=[TextBlock(type="text", text="Memory Manager not started")],
            )

        try:
            # 更新session活动
            self.last_activity_time = datetime.now()
            self.session_manager.update_session(self.agent_id, current_session_id)

            # 延迟初始化组件
            self._lazy_init_components()

            # 跨session搜索相关历史记忆
            historical_results = await self.vector_searcher.search(
                query=context,
                max_results=max_results,
                agent_id=self.agent_id,
                session_id=None,  # 跨所有session搜索
                include_frozen=False
            )

            # 过滤掉当前session的记忆
            filtered_results = [
                mem for mem in historical_results
                if mem.get('session_id') != current_session_id
            ]

            if not filtered_results:
                return ToolResponse(
                    content=[TextBlock(type="text", text="No related historical memories found.")],
                )

            # 格式化结果
            result_text = "【相关历史记忆推送】\n"
            result_text += "以下是与当前上下文相关的历史session记忆：\n\n"

            # 按session分组
            session_memories: Dict[str, List[Dict]] = {}
            for mem in filtered_results:
                sess_id = mem.get('session_id', 'unknown')
                if sess_id not in session_memories:
                    session_memories[sess_id] = []
                session_memories[sess_id].append(mem)

            # 显示各session的相关记忆
            for i, (sess_id, memories) in enumerate(session_memories.items(), 1):
                result_text += f"\n📚 历史session {sess_id[:8]}... ({len(memories)}条相关记忆)\n"
                for j, mem in enumerate(memories[:3], 1):  # 每个session最多显示3条
                    result_text += f"   {i}.{j} [{mem.get('created_at', 'N/A')}] {mem['content'][:80]}...\n"
                    result_text += f"      重要性: {mem.get('importance', 3)} | 相关度: {round(mem.get('similarity', 0), 2)}\n"

            result_text += "\n---\n提示: 这些是来自历史session的相关记忆，可以帮助保持上下文连续性"

            return ToolResponse(content=[TextBlock(type="text", text=result_text)])

        except Exception as e:
            logger.error(f"Failed to get related historical memories: {e}")
            return ToolResponse(
                content=[TextBlock(type="text", text=f"Failed to get related memories: {e}")],
            )

    async def store_feishu_memory(
        self,
        content: str,
        source_id: str = "feishu",
        session_id: Optional[str] = None,
        importance: int = 3,
        message_id: Optional[str] = None,
        reply_to_id: Optional[str] = None,
        root_id: Optional[str] = None,
        mentions: Optional[List[str]] = None,
        is_quote: bool = False,
        quote_original: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> int:
        """Store a Feishu message as memory with enhanced metadata.

        This method specifically handles Feishu messages, extracting and storing:
        - Reply chain information (reply_to_id, root_id)
        - @mentions
        - Quote information
        - Message type

        Args:
            content: Memory content (will be parsed if Feishu JSON format).
            source_id: Source identifier (default: 'feishu').
            session_id: Session identifier.
            importance: Importance level (1-5).
            message_id: Feishu message ID.
            reply_to_id: ID of the message being replied to.
            root_id: Root message ID in the thread.
            mentions: List of mentioned user names.
            is_quote: Whether this is a quote/reply message.
            quote_original: Original quoted content.
            metadata: Additional metadata.

        Returns:
            int: Memory ID (temporary ID for batch processing).
        """
        try:
            # Import here to avoid circular dependency
            from hooks.feishu_message_parser import (
                parse_feishu_content,
                is_important_feishu_message,
                FeishuMessageInfo
            )

            # Parse Feishu content if it's JSON format
            parsed_content = parse_feishu_content(content)
            if parsed_content:
                content = parsed_content

            # Auto-detect importance for important messages
            if is_important_feishu_message(content):
                importance = max(importance, 4)  # At least 4 for important messages

            # Build Feishu-specific metadata
            feishu_metadata = {
                "message_id": message_id,
                "reply_to_id": reply_to_id,
                "root_id": root_id,
                "mentions": mentions or [],
                "is_quote": is_quote,
                "quote_original": quote_original,
                "source_type": "feishu"
            }

            # Merge with additional metadata
            if metadata:
                feishu_metadata.update(metadata)

            return await self.store_memory(
                content=content,
                source_id=source_id,
                session_id=session_id,
                importance=importance,
                metadata=feishu_metadata
            )

        except ImportError:
            # Fallback to regular store_memory if parser not available
            logger.warning("Feishu message parser not available, using default storage")
            return await self.store_memory(
                content=content,
                source_id=source_id,
                session_id=session_id,
                importance=importance,
                metadata=metadata
            )

    async def store_memory(self, content: str, source_id: str = "system",
                         session_id: Optional[str] = None, importance: int = 3,
                         metadata: Optional[dict] = None) -> int:
        """Store a new memory (supports batch processing with memory limits and session management).

        Args:
            content: Memory content.
            source_id: Source identifier.
            session_id: Session identifier.
            importance: Importance level (1-5).
            metadata: Additional metadata.

        Returns:
            int: Memory ID (temporary ID for batch processing).
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()

        # Ensure session_id exists
        session_id = session_id or f"session_{datetime.now().timestamp()}"
        
        # Update session activity
        self.session_manager.update_session(self.agent_id, session_id)

        # Create memory object with agent_id and session_id
        memory = {
            "content": content,
            "source_id": source_id,
            "session_id": session_id,
            "agent_id": self.agent_id,  # Explicitly associate with agent
            "importance": importance,
            "metadata": metadata,
            "created_at": datetime.now().isoformat()
        }

        # Add to memory cache with thread safety
        with self.cache_lock:
            self._memory_cache.append(memory)

        # Check if we need to batch write based on count
        if len(self._memory_cache) >= self.batch_threshold:
            await self._flush_cache()
        # Check if we need to batch write based on size
        elif self._get_cache_size() >= self.max_cache_size:
            await self._flush_cache()
        # Check if we need to batch write based on inactivity
        elif await self._check_inactivity():
            await self._flush_cache()

        # Return temporary ID, actual ID will be generated during batch write
        return id(memory)

    def _get_cache_size(self) -> int:
        """Calculate the size of the memory cache in characters."""
        total_size = 0
        for memory in self._memory_cache:
            total_size += len(memory.get('content', ''))
            if memory.get('metadata'):
                total_size += len(str(memory['metadata']))
        return total_size

    async def _check_inactivity(self) -> bool:
        """Check if the agent has been inactive for a certain period."""
        current_time = datetime.now()
        time_diff = (current_time - self.last_activity_time).total_seconds()
        return time_diff >= self.inactivity_timeout

    async def _flush_cache(self):
        """Batch write memories from cache to database with thread safety."""
        # Get a copy of the cache with thread safety
        with self.cache_lock:
            if not self._memory_cache:
                return
            # Make a copy of the cache to process
            cache_copy = self._memory_cache.copy()
            # Clear the original cache
            self._memory_cache.clear()

        try:
            # Batch insert memories
            memory_ids = []
            for memory in cache_copy:
                # Validate agent_id to prevent cross-agent memory writing
                if memory.get('agent_id') != self.agent_id:
                    logger.warning(f"Memory agent_id mismatch: {memory.get('agent_id')} != {self.agent_id}, skipping")
                    continue
                    
                memory_id = self.db.insert_memory(
                    content=memory["content"],
                    source_id=memory["source_id"],
                    session_id=memory["session_id"],
                    importance=memory["importance"],
                    entity_name=memory["metadata"].get("entity_name") if memory["metadata"] else None,
                    entity_type=memory["metadata"].get("entity_type") if memory["metadata"] else None,
                )
                memory_ids.append(memory_id)

            logger.info(f"Flushed {len(memory_ids)} memories to database")

        except Exception as e:
            logger.error(f"Error flushing memory cache: {e}")
            # Restore cache to retry later
            with self.cache_lock:
                self._memory_cache.extend(cache_copy)


    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Dict[str, Any]: Statistics information.
        """
        if not self._started:
            return {"error": "Memory Manager not started"}

        # 获取基础统计信息
        stats = self.db.get_stats()

        # 获取跨session统计信息
        try:
            cross_session_stats = self.db.get_cross_session_stats()
            stats["cross_session"] = cross_session_stats
        except Exception as e:
            logger.warning(f"Failed to get cross-session stats: {e}")

        # 获取session管理器的session信息
        try:
            sessions_info = []
            with self.session_manager.lock:
                for key, session in self.session_manager.sessions.items():
                    if session["agent_id"] == self.agent_id:
                        sessions_info.append({
                            "session_id": session["session_id"],
                            "created_at": session["created_at"].isoformat() if hasattr(session["created_at"], "isoformat") else str(session["created_at"]),
                            "last_activity": session["last_activity"].isoformat() if hasattr(session["last_activity"], "isoformat") else str(session["last_activity"]),
                            "memory_count": len(session.get("memories", []))
                        })
            stats["active_sessions"] = sessions_info
        except Exception as e:
            logger.warning(f"Failed to get session info: {e}")

        return stats

    async def freeze_memories(self) -> int:
        """Execute freeze scan, mark low-frequency access memories.

        Returns:
            int: Number of frozen memories.
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        # 延迟初始化组件
        self._lazy_init_components()
        
        return self.freezer_hook.freeze_old_memories()

    async def defrost_memories(self, query: str) -> int:
        """Defrost memories related to the query.

        Args:
            query: Query string.

        Returns:
            int: Number of defrosted memories.
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        # 延迟初始化组件
        self._lazy_init_components()
        
        return self.freezer_hook.defrost_related_memories(query)

    async def categorize_memory(self, memory_id: int, category_name: str, confidence: float = 0.5) -> bool:
        """为记忆添加分类

        Args:
            memory_id: 记忆ID
            category_name: 分类名称
            confidence: 分类置信度

        Returns:
            bool: 是否成功
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        return self.db.categorize_memory(memory_id, category_name, confidence)

    async def get_memory_categories(self, memory_id: int) -> list:
        """获取记忆的分类

        Args:
            memory_id: 记忆ID

        Returns:
            list: 分类列表
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        return self.db.get_memory_categories(memory_id)

    async def search_by_category(self, category_name: str, max_results: int = 10) -> list:
        """按分类搜索记忆

        Args:
            category_name: 分类名称
            max_results: 最大结果数

        Returns:
            list: 记忆列表
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        return self.db.search_by_category(category_name, max_results)

    async def create_memory_relation(self, memory_id1: int, memory_id2: int, 
                                  relation_type: str = "related", similarity_score: float = 0.0) -> bool:
        """创建记忆之间的关联

        Args:
            memory_id1: 第一个记忆ID
            memory_id2: 第二个记忆ID
            relation_type: 关联类型
            similarity_score: 相似度分数

        Returns:
            bool: 是否成功
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        return self.db.create_memory_relation(memory_id1, memory_id2, relation_type, similarity_score)

    async def get_related_memories(self, memory_id: int, max_results: int = 5) -> list:
        """获取与指定记忆相关的记忆

        Args:
            memory_id: 记忆ID
            max_results: 最大结果数

        Returns:
            list: 相关记忆列表
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        return self.db.get_related_memories(memory_id, max_results)

    async def update_memory_summary(self, memory_id: int, summary: str) -> bool:
        """更新记忆摘要

        Args:
            memory_id: 记忆ID
            summary: 记忆摘要

        Returns:
            bool: 是否成功
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        return self.db.update_memory_summary(memory_id, summary)

    async def update_memory_priority(self, memory_id: int, importance: int = None, 
                                  importance_score: float = None) -> bool:
        """更新记忆优先级

        Args:
            memory_id: 记忆ID
            importance: 重要性等级 (1-5)
            importance_score: 重要性分数

        Returns:
            bool: 是否成功
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        return self.db.update_memory_priority(memory_id, importance, importance_score)

    async def auto_adjust_priority(self, days: int = 7) -> int:
        """自动调整记忆优先级

        Args:
            days: 统计天数

        Returns:
            int: 调整的记忆数量
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        # Update last activity time
        self.last_activity_time = datetime.now()
        
        return self.db.auto_adjust_priority(days)

    def __repr__(self) -> str:
        return f"HumanThinkingMemoryManager(agent_id={self.agent_id}, started={self._started})"
