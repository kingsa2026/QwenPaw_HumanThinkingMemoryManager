# -*- coding: utf-8 -*-
"""Human Thinking Tool Database Module"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


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

        # 初始化数据库
        self._init_db()

    def _init_db(self):
        """初始化数据库连接和表结构"""
        # 建立数据库连接
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # 创建主表
        self._create_tables()

        # 提交事务
        self.conn.commit()

    def _create_tables(self):
        """创建数据库表结构"""
        # 主表：存储记忆
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS human_thinking_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME,
                source_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                importance INTEGER DEFAULT 3 CHECK(1<=importance<=5),
                is_frozen INTEGER DEFAULT 0 CHECK(0<=is_frozen<=1),
                entity_name TEXT,
                entity_type TEXT,
                embedding_id INTEGER,
                agent_id TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 向量表：存储向量嵌入
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS human_thinking_memory_vectors (
                id INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                vector_dimension INTEGER DEFAULT 384,
                vector_type TEXT DEFAULT 'text-embedding-3-small',
                model_name TEXT DEFAULT 'openai',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 缓存表：存储查询结果缓存
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS human_thinking_vector_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT NOT NULL,
                vector_ids TEXT NOT NULL,
                scores TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                access_count INTEGER DEFAULT 0,
                last_accessed DATETIME
            )
        """)

        # 统计表：存储工具使用统计
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS human_thinking_tool_usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                total_calls INTEGER DEFAULT 0,
                successful_calls INTEGER DEFAULT 0,
                failed_calls INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                last_called DATETIME,
                query_patterns TEXT
            )
        """)

        # 版本表：存储数据库版本信息
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS human_thinking_memory_version (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        self._create_indexes()

        # 插入版本信息
        self._insert_version_info()

    def _create_indexes(self):
        """创建索引优化查询性能"""
        # 主表索引
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON human_thinking_memory(timestamp)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_source_id ON human_thinking_memory(source_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_session_id ON human_thinking_memory(session_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_access_frozen ON human_thinking_memory(last_accessed, is_frozen)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_importance ON human_thinking_memory(importance)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_entity ON human_thinking_memory(entity_name, entity_type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_embedding_id ON human_thinking_memory(embedding_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_agent_id ON human_thinking_memory(agent_id)")

        # 向量表索引
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_vector_type ON human_thinking_memory_vectors(vector_type)")

        # 缓存表索引
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_query_hash ON human_thinking_vector_cache(query_hash)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON human_thinking_vector_cache(expires_at)")

        # 统计表索引
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_tool_name ON human_thinking_tool_usage_stats(tool_name)")

    def _insert_version_info(self):
        """插入版本信息"""
        version_info = [
            ('db_version', '1.0.0', 'Database structure version'),
            ('schema_version', '1', 'Schema version for structure change tracking'),
            ('min_compatible_version', '1.0.0', 'Minimum compatible version'),
            ('last_migration_date', datetime.now().isoformat(), 'Last migration date'),
            ('migration_history', '[]', 'Migration history in JSON format')
        ]

        for key, value, description in version_info:
            self.cursor.execute(
                "INSERT OR REPLACE INTO human_thinking_memory_version (key, value, description) VALUES (?, ?, ?)",
                (key, value, description)
            )

    def insert_memory(self, content: str, source_id: str, session_id: str, 
                     importance: int = 3, entity_name: Optional[str] = None, 
                     entity_type: Optional[str] = None) -> int:
        """插入新记忆

        Args:
            content: 记忆内容
            source_id: 来源标识
            session_id: 会话标识
            importance: 重要性等级 (1-5)
            entity_name: 实体名称
            entity_type: 实体类型

        Returns:
            int: 记忆ID
        """
        self.cursor.execute(
            """
            INSERT INTO human_thinking_memory 
            (content, source_id, session_id, importance, entity_name, entity_type, agent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (content, source_id, session_id, importance, entity_name, entity_type, self.agent_id)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_access_time(self, memory_id: int):
        """更新记忆的访问时间

        Args:
            memory_id: 记忆ID
        """
        self.cursor.execute(
            "UPDATE human_thinking_memory SET last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
            (memory_id,)
        )
        self.conn.commit()

    def get_memory_by_id(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取记忆

        Args:
            memory_id: 记忆ID

        Returns:
            Dict[str, Any]: 记忆信息
        """
        self.cursor.execute(
            "SELECT * FROM human_thinking_memory WHERE id = ?",
            (memory_id,)
        )
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None

    def search_memories(self, query: str, max_results: int = 5, 
                      min_score: float = 0.1) -> List[Dict[str, Any]]:
        """搜索记忆

        Args:
            query: 搜索查询
            max_results: 最大返回结果数
            min_score: 最小相关度分数

        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        # 简单的关键词搜索（实际项目中会使用向量搜索）
        self.cursor.execute(
            """
            SELECT * FROM human_thinking_memory 
            WHERE content LIKE ? AND is_frozen = 0
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
            """,
            (f"%{query}%", max_results)
        )
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        # 总记忆数
        self.cursor.execute("SELECT COUNT(*) FROM human_thinking_memory")
        total_memories = self.cursor.fetchone()[0]

        # 冷藏记忆数
        self.cursor.execute("SELECT COUNT(*) FROM human_thinking_memory WHERE is_frozen = 1")
        frozen_memories = self.cursor.fetchone()[0]

        # 按重要性统计
        self.cursor.execute("SELECT importance, COUNT(*) FROM human_thinking_memory GROUP BY importance")
        importance_stats = dict(self.cursor.fetchall())

        # 最近更新时间
        self.cursor.execute("SELECT MAX(updated_at) FROM human_thinking_memory")
        last_updated = self.cursor.fetchone()[0]

        return {
            "total_memories": total_memories,
            "frozen_memories": frozen_memories,
            "importance_stats": importance_stats,
            "last_updated": last_updated
        }

    def freeze_old_memories(self, days: int = 30, importance_threshold: int = 4) -> int:
        """冷藏旧记忆

        Args:
            days: 天数阈值
            importance_threshold: 重要性阈值

        Returns:
            int: 冷藏的记忆数量
        """
        self.cursor.execute(
            """
            UPDATE human_thinking_memory 
            SET is_frozen = 1 
            WHERE last_accessed < datetime('now', '-' || ? || ' days') 
            AND importance < ?
            """,
            (days, importance_threshold)
        )
        affected = self.cursor.rowcount
        self.conn.commit()
        return affected

    def defrost_related_memories(self, query: str) -> int:
        """解冻与查询相关的记忆

        Args:
            query: 查询字符串

        Returns:
            int: 解冻的记忆数量
        """
        self.cursor.execute(
            """
            UPDATE human_thinking_memory 
            SET is_frozen = 0 
            WHERE content LIKE ? AND is_frozen = 1
            """,
            (f"%{query}%",)
        )
        affected = self.cursor.rowcount
        self.conn.commit()
        return affected

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
        self.cursor.execute(
            """
            INSERT INTO human_thinking_memory_vectors 
            (embedding, vector_dimension, vector_type, model_name)
            VALUES (?, ?, ?, ?)
            """,
            (embedding, vector_dimension, vector_type, model_name)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_vector(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """获取向量嵌入

        Args:
            vector_id: 向量ID

        Returns:
            Dict[str, Any]: 向量信息
        """
        self.cursor.execute(
            "SELECT * FROM human_thinking_memory_vectors WHERE id = ?",
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
        self.cursor.execute(
            "UPDATE human_thinking_memory SET embedding_id = ? WHERE id = ?",
            (vector_id, memory_id)
        )
        self.conn.commit()

    def insert_cache(self, query_hash: str, vector_ids: List[int], 
                    scores: List[float], ttl_seconds: int = 3600):
        """插入缓存

        Args:
            query_hash: 查询哈希
            vector_ids: 向量ID列表
            scores: 分数列表
            ttl_seconds: 缓存有效期（秒）
        """
        expires_at = datetime.now().timestamp() + ttl_seconds
        self.cursor.execute(
            """
            INSERT INTO human_thinking_vector_cache 
            (query_hash, vector_ids, scores, expires_at)
            VALUES (?, ?, ?, datetime('now', '+' || ? || ' seconds'))
            """,
            (query_hash, json.dumps(vector_ids), json.dumps(scores), ttl_seconds)
        )
        self.conn.commit()

    def get_cache(self, query_hash: str) -> Optional[Dict[str, Any]]:
        """获取缓存

        Args:
            query_hash: 查询哈希

        Returns:
            Dict[str, Any]: 缓存信息
        """
        self.cursor.execute(
            """
            SELECT * FROM human_thinking_vector_cache 
            WHERE query_hash = ? AND expires_at > CURRENT_TIMESTAMP
            """,
            (query_hash,)
        )
        row = self.cursor.fetchone()
        if row:
            # 更新访问计数和时间
            self.cursor.execute(
                """
                UPDATE human_thinking_vector_cache 
                SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP 
                WHERE id = ?
                """,
                (row['id'],)
            )
            self.conn.commit()
            return dict(row)
        return None

    def update_stats(self, tool_name: str, success: bool, response_time: float):
        """更新工具使用统计

        Args:
            tool_name: 工具名称
            success: 是否成功
            response_time: 响应时间
        """
        # 检查是否存在记录
        self.cursor.execute(
            "SELECT * FROM human_thinking_tool_usage_stats WHERE tool_name = ?",
            (tool_name,)
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
                UPDATE human_thinking_tool_usage_stats 
                SET total_calls = ?, successful_calls = ?, failed_calls = ?, 
                    avg_response_time = ?, last_called = CURRENT_TIMESTAMP 
                WHERE tool_name = ?
                """,
                (total_calls, successful_calls, failed_calls, avg_response_time, tool_name)
            )
        else:
            # 插入新记录
            self.cursor.execute(
                """
                INSERT INTO human_thinking_tool_usage_stats 
                (tool_name, total_calls, successful_calls, failed_calls, 
                 avg_response_time, last_called)
                VALUES (?, 1, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (tool_name, 1 if success else 0, 0 if success else 1, response_time)
            )
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def __del__(self):
        """析构函数，确保关闭数据库连接"""
        self.close()
