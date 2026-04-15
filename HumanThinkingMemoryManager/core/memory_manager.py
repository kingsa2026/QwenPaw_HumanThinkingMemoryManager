# -*- coding: utf-8 -*-
"""Human Thinking Memory Manager for QwenPaw agents."""
import logging
import platform
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from agentscope.message import Msg, TextBlock
from agentscope.tool import Toolkit, ToolResponse

from qwenpaw.agents.memory.base_memory_manager import BaseMemoryManager
from qwenpaw.agents.model_factory import create_model_and_formatter
from qwenpaw.agents.tools import read_file, write_file, edit_file
from qwenpaw.agents.utils import get_token_counter
from qwenpaw.config import load_config
from qwenpaw.config.config import load_agent_config
from qwenpaw.constant import EnvVarLoader

# 动态路径解析 - 确保无论模块放在哪个位置都能正确导入
def _get_module_path() -> Path:
    """动态获取当前模块的路径。

    使用 __file__ 来确定模块的实际位置，
    确保无论 HumanThinkingMemoryManager 文件夹放在哪里都能正确工作。
    """
    return Path(__file__).resolve().parent

def _ensure_qwenpaw_path() -> None:
    """确保 qwenpaw 路径在 sys.path 中，以便正确导入子模块。"""
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

# 在导入子模块之前确保路径正确
_ensure_qwenpaw_path()

# 动态导入子模块
from .database import HumanThinkingMemoryDB
from ..search.vector import VectorSearch, FallbackVectorSearch
from ..hooks.memory_hooks import MemoryRetrievalHook, MemoryWriteHook, MemoryFreezerHook
from ..utils.migrator import MemoryMigrator
from ..utils.version import VersionManager

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
        self.vector_search: Optional[VectorSearch] = None
        self.fallback_vector_search: Optional[FallbackVectorSearch] = None

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
        1. 初始化数据库
        2. 检查版本并升级
        3. 初始化搜索引擎
        4. 初始化钩子
        5. 执行数据迁移（如果有）
        """
        if self._started:
            logger.warning("Memory Manager already started")
            return None

        logger.info(f"Starting HumanThinkingMemoryManager for agent: {self.agent_id}")

        # 1. 初始化数据库
        self.db = HumanThinkingMemoryDB(
            db_path=str(self.db_path),
            agent_id=self.agent_id,
        )

        # 2. 检查版本并升级
        self.version_manager = VersionManager(self.db.conn)
        if self.version_manager.need_upgrade():
            logger.info("Upgrading database...")
            self.version_manager.upgrade(str(self.db_path))

        # 3. 初始化搜索引擎
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

        if vector_enabled:
            self.vector_search = VectorSearch(self.db, self.agent_id)
        else:
            self.fallback_vector_search = FallbackVectorSearch(self.db, self.agent_id)

        # 4. 初始化钩子
        self.retrieval_hook = MemoryRetrievalHook(self.db, self.agent_id)
        self.write_hook = MemoryWriteHook(self.db, self.agent_id)
        self.freezer_hook = MemoryFreezerHook(self.db, self.agent_id)

        # 5. 执行数据迁移
        self.migrator = MemoryMigrator(
            workspace_dir=self.working_dir,
            agent_id=self.agent_id,
            db=self.db,
        )
        await self.migrator.migrate_if_needed()

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

        # 等待摘要任务完成
        await self.await_summary_tasks()

        # 关闭数据库连接
        if self.db:
            self.db.close()
            self.db = None

        self._started = False
        logger.info(f"HumanThinkingMemoryManager closed for agent: {self.agent_id}")
        return True

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

    async def memory_search(
        self,
        query: str,
        max_results: int = 5,
        min_score: float = 0.1,
    ) -> ToolResponse:
        """Search stored memories for relevant content.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.
            min_score: Minimum relevance score.

        Returns:
            ToolResponse: Response containing search results.
        """
        if not self._started:
            return ToolResponse(
                content=[TextBlock(type="text", text="Memory Manager not started")],
            )

        try:
            # 执行搜索
            if self.vector_search:
                results = self.vector_search.search_similar(
                    query_text=query,
                    top_k=max_results,
                    min_score=min_score,
                )
            else:
                results = self.fallback_vector_search.search_similar(
                    query_text=query,
                    top_k=max_results,
                    min_score=min_score,
                )

            # 格式化结果
            if not results:
                return ToolResponse(
                    content=[TextBlock(type="text", text="No relevant memories found.")],
                )

            result_text = "【相关记忆】\n\n"
            for i, mem in enumerate(results, 1):
                result_text += f"{i}. [{mem['timestamp']}] {mem['content']}\n"
                result_text += f"   重要性: {mem['importance']} | 相关度: {mem.get('score', 'N/A')}\n\n"

            # 更新访问时间
            for mem in results:
                if 'id' in mem:
                    self.db.update_access_time(mem["id"])

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

    async def store_memory(self, content: str, source_id: str = "system",
                         session_id: Optional[str] = None, importance: int = 3,
                         metadata: Optional[dict] = None) -> int:
        """Store a new memory.

        Args:
            content: Memory content.
            source_id: Source identifier.
            session_id: Session identifier.
            importance: Importance level (1-5).
            metadata: Additional metadata.

        Returns:
            int: Memory ID.
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

        memory_id = self.db.insert_memory(
            content=content,
            source_id=source_id,
            session_id=session_id or self.agent_id,
            importance=importance,
            entity_name=metadata.get("entity_name") if metadata else None,
            entity_type=metadata.get("entity_type") if metadata else None,
        )

        # 更新向量索引
        if self.vector_search:
            await self.vector_search.add_embedding(memory_id, content)

        return memory_id

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics.

        Returns:
            Dict[str, Any]: Statistics information.
        """
        if not self._started:
            return {"error": "Memory Manager not started"}

        return self.db.get_stats()

    async def freeze_memories(self) -> int:
        """Execute freeze scan, mark low-frequency access memories.

        Returns:
            int: Number of frozen memories.
        """
        if not self._started:
            raise RuntimeError("Memory Manager not started")

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

        return self.freezer_hook.defrost_related_memories(query)

    def __repr__(self) -> str:
        return f"HumanThinkingMemoryManager(agent_id={self.agent_id}, started={self._started})"
