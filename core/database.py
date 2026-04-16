# -*- coding: utf-8 -*-
"""Human Thinking Tool Database Module"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

__version__ = "1.0.2-beta0.2"

# 数据库版本
CURRENT_DB_VERSION = "1.0.2-beta0.2"


class HumanThinkingMemoryDB:
    """Human Thinking Memory Database"""

    def __init__(self, db_path: str, agent_id: str):
        """初始化数据库

        Args:
            db_path: 数据库文件路径
            agent_id: Agent ID
        """
        self.db_path = db_path
        self.agent_id = agent_id
        self.conn = None
        self.cursor = None

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_db()

    def _init_db(self):
        """初始化数据库连接和表结构"""
        # 建立数据库连接
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # 创建主表
        self._create_tables()

        # 提交事务
        self.conn.commit()

    def _create_tables(self):
        """创建数据库表结构"""
        # 1. 版本管理表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                db_version TEXT NOT NULL DEFAULT '1.0.0',
                schema_version TEXT NOT NULL DEFAULT '1.0.0',
                min_compatible_version TEXT NOT NULL DEFAULT '1.0.0',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                upgrade_history TEXT DEFAULT '[]'
            )
        """)

        # 2. 记忆主表（增强版）
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS qwenpaw_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                content_embedding TEXT,
                content_summary TEXT,
                source_id TEXT DEFAULT 'user',
                source_type TEXT DEFAULT 'text',
                session_id TEXT,
                agent_id TEXT NOT NULL,
                importance INTEGER DEFAULT 3,
                importance_score REAL DEFAULT 0.0,
                access_count INTEGER DEFAULT 0,
                search_count INTEGER DEFAULT 0,
                search_score REAL DEFAULT 0.0,
                access_frozen INTEGER DEFAULT 0,
                last_accessed_at DATETIME,
                last_searched_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                metadata TEXT DEFAULT '{}',
                tags TEXT DEFAULT '[]'
            )
        """)

        # 3. 向量表（增强版）
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_vectors (
                id INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                embedding_id TEXT UNIQUE,
                vector_dimension INTEGER DEFAULT 384,
                vector_type TEXT DEFAULT 'text-embedding',
                model_name TEXT DEFAULT 'default',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id) REFERENCES qwenpaw_memory(id)
                    ON DELETE CASCADE ON UPDATE CASCADE
            )
        """)

        # 4. 向量缓存表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS qwenpaw_vector_cache (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT,
                vector_ids TEXT NOT NULL,
                similarity_scores TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                access_count INTEGER DEFAULT 0,
                hit_count INTEGER DEFAULT 0
            )
        """)

        # 5. 记忆关联表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id1 INTEGER NOT NULL,
                memory_id2 INTEGER NOT NULL,
                relation_type TEXT DEFAULT 'related',
                similarity_score REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id1) REFERENCES qwenpaw_memory(id) ON DELETE CASCADE,
                FOREIGN KEY (memory_id2) REFERENCES qwenpaw_memory(id) ON DELETE CASCADE,
                UNIQUE (memory_id1, memory_id2)
            )
        """)

        # 6. 记忆分类表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL UNIQUE,
                category_description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. 记忆分类关联表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_category_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                confidence REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES qwenpaw_memory(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES qwenpaw_memory_categories(id) ON DELETE CASCADE,
                UNIQUE (memory_id, category_id)
            )
        """)

        # 8. 工具使用统计表
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS qwenpaw_tool_usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                total_calls INTEGER DEFAULT 0,
                successful_calls INTEGER DEFAULT 0,
                failed_calls INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0.0,
                last_called_at DATETIME,
                query_patterns TEXT DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        self._create_indexes()

        # 插入版本信息
        self._insert_version_info()

    def _create_indexes(self):
        """创建索引优化查询性能"""
        # 6. 索引创建
        indexes = [
            # 主表索引
            "CREATE INDEX IF NOT EXISTS idx_memory_agent ON qwenpaw_memory(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_session ON qwenpaw_memory(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_importance ON qwenpaw_memory(importance)",
            "CREATE INDEX IF NOT EXISTS idx_memory_frozen ON qwenpaw_memory(access_frozen)",
            "CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON qwenpaw_memory(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_memory_source ON qwenpaw_memory(source_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_access ON qwenpaw_memory(last_accessed_at)",
            
            # 复合索引
            "CREATE INDEX IF NOT EXISTS idx_memory_full_join ON qwenpaw_memory(id, agent_id)",
            
            # 向量表索引
            "CREATE INDEX IF NOT EXISTS idx_vector_metadata ON qwenpaw_memory_vectors(id, vector_type, vector_dimension)",
            
            # 缓存表索引
            "CREATE INDEX IF NOT EXISTS idx_cache_expires ON qwenpaw_vector_cache(expires_at)",
            
            # 工具统计索引
            "CREATE INDEX IF NOT EXISTS idx_tool_stats_agent ON qwenpaw_tool_usage_stats(agent_id, tool_name)",
            
            # 记忆关联表索引
            "CREATE INDEX IF NOT EXISTS idx_memory_relations_1 ON qwenpaw_memory_relations(memory_id1)",
            "CREATE INDEX IF NOT EXISTS idx_memory_relations_2 ON qwenpaw_memory_relations(memory_id2)",
            
            # 记忆分类关联表索引
            "CREATE INDEX IF NOT EXISTS idx_memory_category_relations ON qwenpaw_memory_category_relations(memory_id, category_id)"
        ]
        
        for idx_sql in indexes:
            try:
                self.cursor.execute(idx_sql)
            except sqlite3.Error as e:
                logger.warning(f"索引创建失败: {e}")

    def _insert_version_info(self):
        """插入版本信息"""
        # 初始化版本信息
        self.cursor.execute("SELECT COUNT(*) FROM qwenpaw_memory_version")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO qwenpaw_memory_version 
                (db_version, schema_version, min_compatible_version)
                VALUES (?, ?, ?)
            """, (CURRENT_DB_VERSION, CURRENT_DB_VERSION, "1.0.0"))

    @contextmanager
    def _transaction(self):
        """事务上下文管理器"""
        try:
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def get_version(self) -> Dict[str, str]:
        """获取数据库版本信息"""
        self.cursor.execute("""
            SELECT db_version, schema_version, min_compatible_version, 
                   created_at, updated_at, upgrade_history
            FROM qwenpaw_memory_version LIMIT 1
        """)
        row = self.cursor.fetchone()
        if row:
            return {
                "db_version": row[0],
                "schema_version": row[1],
                "min_compatible_version": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "upgrade_history": json.loads(row[5] or "[]")
            }
        return {}

    def insert_memory(self, content: str, source_id: str, session_id: str, 
                     importance: int = 3, entity_name: Optional[str] = None, 
                     entity_type: Optional[str] = None, metadata: Optional[Dict] = None,
                     tags: Optional[List[str]] = None, content_embedding: Optional[str] = None,
                     content_summary: Optional[str] = None) -> int:
        """插入新记忆

        Args:
            content: 记忆内容
            source_id: 来源标识
            session_id: 会话标识
            importance: 重要性等级 (1-5)
            entity_name: 实体名称
            entity_type: 实体类型
            metadata: 元数据
            tags: 标签列表
            content_embedding: 内容嵌入向量
            content_summary: 内容摘要

        Returns:
            int: 记忆ID
        """
        with self._transaction():
            self.cursor.execute(
                """
                INSERT INTO qwenpaw_memory 
                (content, content_embedding, content_summary, source_id, source_type,
                 session_id, agent_id, importance, metadata, tags, last_accessed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    content,
                    content_embedding,
                    content_summary,
                    source_id,
                    "text",
                    session_id,
                    self.agent_id,
                    importance,
                    json.dumps(metadata or {}),
                    json.dumps(tags or []),
                )
            )
            return self.cursor.lastrowid

    def get_memory_by_id(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取记忆

        Args:
            memory_id: 记忆ID

        Returns:
            Dict[str, Any]: 记忆信息
        """
        self.cursor.execute(
            """
            SELECT id, content, content_embedding, content_summary,
                   source_id, source_type, session_id, agent_id, importance,
                   importance_score, access_count, access_frozen,
                   last_accessed_at, created_at, updated_at, metadata, tags
            FROM qwenpaw_memory
            WHERE id = ? AND deleted_at IS NULL
            """,
            (memory_id,)
        )
        row = self.cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "content": row[1],
                "content_embedding": row[2],
                "content_summary": row[3],
                "source_id": row[4],
                "source_type": row[5],
                "session_id": row[6],
                "agent_id": row[7],
                "importance": row[8],
                "importance_score": row[9],
                "access_count": row[10],
                "access_frozen": row[11],
                "last_accessed_at": row[12],
                "created_at": row[13],
                "updated_at": row[14],
                "metadata": json.loads(row[15] or "{}"),
                "tags": json.loads(row[16] or "[]")
            }
        return None

    def search_by_text(
        self,
        query: str,
        max_results: int = 5,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        include_frozen: bool = False
    ) -> List[Dict[str, Any]]:
        """
        基于文本搜索记忆

        Args:
            query: 搜索查询
            max_results: 最大结果数
            agent_id: Agent ID（可选，默认当前）
            session_id: 会话ID，用于过滤特定会话的记忆
            include_frozen: 是否包含冷藏记忆

        Returns:
            记忆列表
        """
        search_agent = agent_id or self.agent_id
        
        # 使用 LIKE 搜索（备选方案）
        search_pattern = f"%{query}%"
        
        sql = """
            SELECT id, content, content_summary, source_id, session_id,
                   importance, importance_score, access_count, access_frozen,
                   last_accessed_at, created_at, metadata, tags
            FROM qwenpaw_memory
            WHERE agent_id = ?
              AND content LIKE ?
              AND deleted_at IS NULL
        """
        
        params = [search_agent, search_pattern]
        
        # 添加会话过滤
        if session_id:
            sql += " AND session_id = ?"
            params.append(session_id)
        
        if not include_frozen:
            sql += " AND access_frozen = 0"
        
        sql += " ORDER BY importance DESC, access_count DESC, last_accessed_at DESC LIMIT ?"
        params.append(max_results)
        
        self.cursor.execute(sql, params)
        
        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1],
                "content_summary": row[2],
                "source_id": row[3],
                "session_id": row[4],
                "importance": row[5],
                "importance_score": row[6],
                "access_count": row[7],
                "access_frozen": row[8],
                "last_accessed_at": row[9],
                "created_at": row[10],
                "metadata": json.loads(row[11] or "{}"),
                "tags": json.loads(row[12] or "[]"),
                "score": 0.5  # 模拟相似度分数
            })
        
        return results

    def search_by_vector(
        self,
        vector: bytes,
        max_results: int = 5,
        agent_id: Optional[str] = None,
        vector_type: str = "text-embedding"
    ) -> List[Tuple[int, float]]:
        """
        基于向量搜索记忆

        Args:
            vector: 向量数据
            max_results: 最大结果数
            agent_id: Agent ID
            vector_type: 向量类型

        Returns:
            [(记忆ID, 相似度), ...]
        """
        # 简化实现：返回空列表
        # 实际向量搜索由 VectorSearcher 处理
        return []

    def update_memory_access(self, memory_id: int):
        """更新记忆访问信息"""
        with self._transaction():
            self.cursor.execute(
                """
                UPDATE qwenpaw_memory
                SET access_count = access_count + 1,
                    last_accessed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (memory_id,)
            )

    def update_memory_search(self, memory_id: int, similarity: float):
        """更新记忆搜索信息

        Args:
            memory_id: 记忆ID
            similarity: 搜索相似度
        """
        with self._transaction():
            self.cursor.execute(
                """
                UPDATE qwenpaw_memory
                SET search_count = search_count + 1,
                    search_score = search_score + ?,
                    importance_score = importance_score + (? * 0.1),
                    last_searched_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (similarity, similarity, memory_id)
            )

    def batch_update_memory_search(self, memory_ids: List[int], scores: List[float]):
        """批量更新记忆搜索信息

        Args:
            memory_ids: 记忆ID列表
            scores: 相似度分数列表
        """
        if not memory_ids or not scores or len(memory_ids) != len(scores):
            return
        
        with self._transaction():
            # 批量更新，减少数据库操作次数
            for memory_id, score in zip(memory_ids, scores):
                self.cursor.execute(
                    """
                    UPDATE qwenpaw_memory
                    SET search_count = search_count + 1,
                        search_score = search_score + ?,
                        importance_score = importance_score + (? * 0.1),
                        last_searched_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (score, score, memory_id)
                )

    def freeze_memory(self, memory_id: int) -> bool:
        """冷藏记忆"""
        with self._transaction():
            self.cursor.execute(
                """
                UPDATE qwenpaw_memory
                SET access_frozen = 1
                WHERE id = ?
                """,
                (memory_id,)
            )
            return self.cursor.rowcount > 0

    def defrost_memory(self, memory_id: int) -> bool:
        """解冻记忆"""
        with self._transaction():
            self.cursor.execute(
                """
                UPDATE qwenpaw_memory
                SET access_frozen = 0,
                    last_accessed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (memory_id,)
            )
            return self.cursor.rowcount > 0

    def delete_memory(self, memory_id: int) -> bool:
        """删除记忆（软删除）"""
        with self._transaction():
            self.cursor.execute(
                """
                UPDATE qwenpaw_memory
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (memory_id,)
            )
            return self.cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        # 总记忆数
        self.cursor.execute("""
            SELECT COUNT(*) FROM qwenpaw_memory 
            WHERE agent_id = ? AND deleted_at IS NULL
        """, (self.agent_id,))
        total_memories = self.cursor.fetchone()[0]

        # 冷藏记忆数
        self.cursor.execute("""
            SELECT COUNT(*) FROM qwenpaw_memory 
            WHERE agent_id = ? AND access_frozen = 1 AND deleted_at IS NULL
        """, (self.agent_id,))
        frozen_memories = self.cursor.fetchone()[0]

        # 按重要性统计
        self.cursor.execute("""
            SELECT importance, COUNT(*) 
            FROM qwenpaw_memory 
            WHERE agent_id = ? AND deleted_at IS NULL
            GROUP BY importance
        """, (self.agent_id,))
        importance_stats = dict(self.cursor.fetchall())

        # 最近访问
        self.cursor.execute("""
            SELECT COUNT(*) FROM qwenpaw_memory 
            WHERE agent_id = ? 
              AND last_accessed_at > datetime('now', '-7 days')
              AND deleted_at IS NULL
        """, (self.agent_id,))
        recent_access = self.cursor.fetchone()[0]

        # 最近更新时间
        self.cursor.execute("""
            SELECT MAX(updated_at) FROM qwenpaw_memory 
            WHERE agent_id = ? AND deleted_at IS NULL
        """, (self.agent_id,))
        last_updated = self.cursor.fetchone()[0]

        stats = {
            "total_memories": total_memories,
            "frozen_memories": frozen_memories,
            "importance_stats": importance_stats,
            "recent_access": recent_access,
            "last_updated": last_updated,
            "db_version": self.get_version().get("db_version", "unknown")
        }

        return stats

    def freeze_old_memories(self, days: int = 30, importance_threshold: int = 4) -> int:
        """冷藏旧记忆

        Args:
            days: 天数阈值
            importance_threshold: 重要性阈值

        Returns:
            int: 冷藏的记忆数量
        """
        with self._transaction():
            self.cursor.execute(
                """
                UPDATE qwenpaw_memory 
                SET access_frozen = 1 
                WHERE agent_id = ?
                  AND last_accessed_at < datetime('now', '-' || ? || ' days') 
                  AND importance < ?
                  AND deleted_at IS NULL
                """,
                (self.agent_id, days, importance_threshold)
            )
            return self.cursor.rowcount

    def defrost_related_memories(self, query: str) -> int:
        """解冻与查询相关的记忆

        Args:
            query: 查询字符串

        Returns:
            int: 解冻的记忆数量
        """
        with self._transaction():
            self.cursor.execute(
                """
                UPDATE qwenpaw_memory 
                SET access_frozen = 0 
                WHERE agent_id = ?
                  AND content LIKE ? 
                  AND access_frozen = 1
                  AND deleted_at IS NULL
                """,
                (self.agent_id, f"%{query}%")
            )
            return self.cursor.rowcount

    def insert_vector(self, embedding: bytes, vector_dimension: int = 384, 
                     vector_type: str = 'text-embedding-3-small', 
                     model_name: str = 'openai') -> int:
        """插入向量嵌入

        Args:
            embedding: 向量嵌入数据
            vector_dimension: 向量维度
            vector_type: 向量类型
            model_name: 模型名称

        Returns:
            int: 向量ID
        """
        with self._transaction():
            self.cursor.execute(
                """
                INSERT INTO qwenpaw_memory_vectors 
                (embedding, vector_dimension, vector_type, model_name)
                VALUES (?, ?, ?, ?)
                """,
                (embedding, vector_dimension, vector_type, model_name)
            )
            return self.cursor.lastrowid

    def get_vector(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """获取向量嵌入

        Args:
            vector_id: 向量ID

        Returns:
            Dict[str, Any]: 向量信息
        """
        self.cursor.execute(
            "SELECT * FROM qwenpaw_memory_vectors WHERE id = ?",
            (vector_id,)
        )
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None

    def update_memory_vector(self, memory_id: int, vector_id: int):
        """更新记忆的向量ID

        Args:
            memory_id: 记忆ID
            vector_id: 向量ID
        """
        with self._transaction():
            self.cursor.execute(
                "UPDATE qwenpaw_memory SET embedding_id = ? WHERE id = ?",
                (vector_id, memory_id)
            )

    def insert_cache(self, query_hash: str, query_text: str, vector_ids: List[int], 
                    scores: List[float], ttl_seconds: int = 3600):
        """插入缓存

        Args:
            query_hash: 查询哈希
            query_text: 查询文本
            vector_ids: 向量ID列表
            scores: 分数列表
            ttl_seconds: 缓存有效期（秒）
        """
        with self._transaction():
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO qwenpaw_vector_cache 
                (query_hash, query_text, vector_ids, similarity_scores, expires_at)
                VALUES (?, ?, ?, ?, datetime('now', '+' || ? || ' seconds'))
                """,
                (query_hash, query_text[:200], json.dumps(vector_ids), json.dumps(scores), ttl_seconds)
            )

    def get_cache(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """获取缓存

        Args:
            query_hash: 查询哈希

        Returns:
            Dict[str, Any]: 缓存信息
        """
        self.cursor.execute(
            """
            SELECT * FROM qwenpaw_vector_cache 
            WHERE query_hash = ? AND expires_at > CURRENT_TIMESTAMP
            """,
            (query_hash,)
        )
        row = self.cursor.fetchone()
        if row:
            # 更新命中计数
            self.cursor.execute(
                """
                UPDATE qwenpaw_vector_cache 
                SET access_count = access_count + 1,
                    hit_count = hit_count + 1
                WHERE query_hash = ?
                """,
                (query_hash,)
            )
            self.conn.commit()
            return dict(row)
        return None

    def clear_expired_cache(self):
        """清除过期缓存"""
        with self._transaction():
            self.cursor.execute(
                "DELETE FROM qwenpaw_vector_cache WHERE expires_at < CURRENT_TIMESTAMP"
            )

    def update_stats(self, tool_name: str, success: bool, response_time: float):
        """更新工具使用统计

        Args:
            tool_name: 工具名称
            success: 是否成功
            response_time: 响应时间
        """
        with self._transaction():
            # 检查是否存在记录
            self.cursor.execute(
                "SELECT * FROM qwenpaw_tool_usage_stats WHERE tool_name = ? AND agent_id = ?",
                (tool_name, self.agent_id)
            )
            row = self.cursor.fetchone()

            if row:
                # 更新现有记录
                total_calls = row['total_calls'] + 1
                successful_calls = row['successful_calls'] + (1 if success else 0)
                failed_calls = row['failed_calls'] + (0 if success else 1)
                avg_response_time = ((row['avg_response_time'] * row['total_calls']) + response_time) / total_calls

                self.cursor.execute(
                    """
                    UPDATE qwenpaw_tool_usage_stats 
                    SET total_calls = ?, successful_calls = ?, failed_calls = ?, 
                        avg_response_time = ?, last_called_at = CURRENT_TIMESTAMP 
                    WHERE tool_name = ? AND agent_id = ?
                    """,
                    (total_calls, successful_calls, failed_calls, avg_response_time, tool_name, self.agent_id)
                )
            else:
                # 插入新记录
                self.cursor.execute(
                    """
                    INSERT INTO qwenpaw_tool_usage_stats 
                    (tool_name, agent_id, total_calls, successful_calls, failed_calls, 
                     avg_response_time, last_called_at)
                    VALUES (?, ?, 1, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (tool_name, self.agent_id, 1 if success else 0, 0 if success else 1, response_time)
                )

    def compact_database(self) -> int:
        """
        压缩数据库

        Returns:
            释放的页面数
        """
        with self._transaction():
            # 删除已标记的记录
            self.cursor.execute("DELETE FROM qwenpaw_memory WHERE deleted_at IS NOT NULL")
            deleted_count = self.cursor.rowcount
            
            # 清除过期缓存
            self.clear_expired_cache()
            
            # VACUUM
            self.conn.execute("VACUUM")
            
            return deleted_count

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def insert_category(self, category_name: str, category_description: str = "") -> int:
        """插入记忆分类

        Args:
            category_name: 分类名称
            category_description: 分类描述

        Returns:
            int: 分类ID
        """
        with self._transaction():
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO qwenpaw_memory_categories 
                (category_name, category_description)
                VALUES (?, ?)
                """,
                (category_name, category_description)
            )
            # 获取分类ID
            self.cursor.execute(
                "SELECT id FROM qwenpaw_memory_categories WHERE category_name = ?",
                (category_name,)
            )
            row = self.cursor.fetchone()
            return row[0] if row else None

    def categorize_memory(self, memory_id: int, category_name: str, confidence: float = 0.5) -> bool:
        """为记忆添加分类

        Args:
            memory_id: 记忆ID
            category_name: 分类名称
            confidence: 分类置信度

        Returns:
            bool: 是否成功
        """
        # 获取或创建分类
        category_id = self.insert_category(category_name)
        if not category_id:
            return False

        with self._transaction():
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO qwenpaw_memory_category_relations 
                (memory_id, category_id, confidence)
                VALUES (?, ?, ?)
                """,
                (memory_id, category_id, confidence)
            )
            return self.cursor.rowcount > 0

    def get_memory_categories(self, memory_id: int) -> List[Dict[str, Any]]:
        """获取记忆的分类

        Args:
            memory_id: 记忆ID

        Returns:
            List[Dict[str, Any]]: 分类列表
        """
        self.cursor.execute(
            """
            SELECT c.id, c.category_name, c.category_description, r.confidence
            FROM qwenpaw_memory_categories c
            JOIN qwenpaw_memory_category_relations r ON c.id = r.category_id
            WHERE r.memory_id = ?
            """,
            (memory_id,)
        )
        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "category_name": row[1],
                "category_description": row[2],
                "confidence": row[3]
            })
        return results

    def search_by_category(self, category_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """按分类搜索记忆

        Args:
            category_name: 分类名称
            max_results: 最大结果数

        Returns:
            List[Dict[str, Any]]: 记忆列表
        """
        self.cursor.execute(
            """
            SELECT m.id, m.content, m.content_summary, m.source_id, m.session_id,
                   m.importance, m.importance_score, m.access_count, m.access_frozen,
                   m.last_accessed_at, m.created_at, m.metadata, m.tags,
                   r.confidence
            FROM qwenpaw_memory m
            JOIN qwenpaw_memory_category_relations r ON m.id = r.memory_id
            JOIN qwenpaw_memory_categories c ON r.category_id = c.id
            WHERE c.category_name = ? AND m.agent_id = ? AND m.deleted_at IS NULL
            ORDER BY r.confidence DESC, m.importance DESC, m.last_accessed_at DESC
            LIMIT ?
            """,
            (category_name, self.agent_id, max_results)
        )
        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1],
                "content_summary": row[2],
                "source_id": row[3],
                "session_id": row[4],
                "importance": row[5],
                "importance_score": row[6],
                "access_count": row[7],
                "access_frozen": row[8],
                "last_accessed_at": row[9],
                "created_at": row[10],
                "metadata": json.loads(row[11] or "{}"),
                "tags": json.loads(row[12] or "[]"),
                "category_confidence": row[13]
            })
        return results

    def create_memory_relation(self, memory_id1: int, memory_id2: int, 
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
        # 确保memory_id1 < memory_id2，避免重复
        if memory_id1 > memory_id2:
            memory_id1, memory_id2 = memory_id2, memory_id1

        with self._transaction():
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO qwenpaw_memory_relations 
                (memory_id1, memory_id2, relation_type, similarity_score)
                VALUES (?, ?, ?, ?)
                """,
                (memory_id1, memory_id2, relation_type, similarity_score)
            )
            return self.cursor.rowcount > 0

    def get_related_memories(self, memory_id: int, max_results: int = 5) -> List[Dict[str, Any]]:
        """获取与指定记忆相关的记忆

        Args:
            memory_id: 记忆ID
            max_results: 最大结果数

        Returns:
            List[Dict[str, Any]]: 相关记忆列表
        """
        self.cursor.execute(
            """
            SELECT m.id, m.content, m.content_summary, m.source_id, m.session_id,
                   m.importance, m.importance_score, m.access_count, m.access_frozen,
                   m.last_accessed_at, m.created_at, m.metadata, m.tags,
                   r.relation_type, r.similarity_score
            FROM qwenpaw_memory m
            JOIN qwenpaw_memory_relations r ON 
                (m.id = r.memory_id1 AND r.memory_id2 = ?) OR 
                (m.id = r.memory_id2 AND r.memory_id1 = ?)
            WHERE m.agent_id = ? AND m.deleted_at IS NULL
            ORDER BY r.similarity_score DESC, m.importance DESC, m.last_accessed_at DESC
            LIMIT ?
            """,
            (memory_id, memory_id, self.agent_id, max_results)
        )
        results = []
        for row in self.cursor.fetchall():
            results.append({
                "id": row[0],
                "content": row[1],
                "content_summary": row[2],
                "source_id": row[3],
                "session_id": row[4],
                "importance": row[5],
                "importance_score": row[6],
                "access_count": row[7],
                "access_frozen": row[8],
                "last_accessed_at": row[9],
                "created_at": row[10],
                "metadata": json.loads(row[11] or "{}"),
                "tags": json.loads(row[12] or "[]"),
                "relation_type": row[13],
                "similarity_score": row[14]
            })
        return results

    def update_memory_summary(self, memory_id: int, summary: str) -> bool:
        """更新记忆摘要

        Args:
            memory_id: 记忆ID
            summary: 记忆摘要

        Returns:
            bool: 是否成功
        """
        with self._transaction():
            self.cursor.execute(
                """
                UPDATE qwenpaw_memory
                SET content_summary = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (summary, memory_id)
            )
            return self.cursor.rowcount > 0

    def update_memory_priority(self, memory_id: int, importance: Optional[int] = None, 
                             importance_score: Optional[float] = None) -> bool:
        """更新记忆优先级

        Args:
            memory_id: 记忆ID
            importance: 重要性等级 (1-5)
            importance_score: 重要性分数

        Returns:
            bool: 是否成功
        """
        with self._transaction():
            if importance is not None and importance_score is not None:
                self.cursor.execute(
                    """
                    UPDATE qwenpaw_memory
                    SET importance = ?, importance_score = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (importance, importance_score, memory_id)
                )
            elif importance is not None:
                self.cursor.execute(
                    """
                    UPDATE qwenpaw_memory
                    SET importance = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (importance, memory_id)
                )
            elif importance_score is not None:
                self.cursor.execute(
                    """
                    UPDATE qwenpaw_memory
                    SET importance_score = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (importance_score, memory_id)
                )
            else:
                return False
            return self.cursor.rowcount > 0

    def auto_adjust_priority(self, days: int = 7) -> int:
        """自动调整记忆优先级

        Args:
            days: 统计天数

        Returns:
            int: 调整的记忆数量
        """
        with self._transaction():
            # 基于访问频率和搜索频率调整重要性
            self.cursor.execute(
                """
                UPDATE qwenpaw_memory
                SET 
                    importance = CASE 
                        WHEN access_count > 10 OR search_count > 5 THEN 5
                        WHEN access_count > 5 OR search_count > 3 THEN 4
                        WHEN access_count > 1 OR search_count > 0 THEN 3
                        ELSE 2
                    END,
                    importance_score = (access_count * 0.5) + (search_count * 1.0),
                    updated_at = CURRENT_TIMESTAMP
                WHERE agent_id = ?
                  AND last_accessed_at > datetime('now', '-' || ? || ' days')
                  AND deleted_at IS NULL
                """,
                (self.agent_id, days)
            )
            return self.cursor.rowcount

    def __del__(self):
        """析构函数，确保关闭数据库连接"""
        self.close()
