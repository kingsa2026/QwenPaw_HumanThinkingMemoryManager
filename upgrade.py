#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Human Thinking Memory Manager 统一升级脚本

支持从任意旧版本升级到最新版本
自动检测当前版本并执行必要的数据库迁移
"""

import os
import sys
import json
import shutil
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 版本顺序（用于比较版本）
VERSION_ORDER = [
    "1.0.0",
    "1.0.1",
    "1.0.2",
    "1.0.2-beta0.1",
    "1.0.2-beta0.2",
    "1.0.2-beta0.3",
    "1.0.5",  # 特殊版本，作为中间过渡
]

# 最新版本
LATEST_VERSION = "1.0.2-beta0.3"


def compare_versions(v1: str, v2: str) -> int:
    """比较两个版本号

    Args:
        v1: 版本号1
        v2: 版本号2

    Returns:
        1 if v1 > v2, -1 if v1 < v2, 0 if equal
    """
    def normalize_version(v: str) -> tuple:
        # 处理beta版本
        if '-' in v:
            parts = v.split('-')
            main_parts = [int(p) for p in parts[0].split('.')]
            beta_part = parts[1] if len(parts) > 1 else ""
            return main_parts, beta_part
        else:
            parts = [int(p) for p in v.split('.')]
            return parts, ""

    main1, beta1 = normalize_version(v1)
    main2, beta2 = normalize_version(v2)

    # 比较主版本号
    for i in range(max(len(main1), len(main2))):
        p1 = main1[i] if i < len(main1) else 0
        p2 = main2[i] if i < len(main2) else 0
        if p1 > p2:
            return 1
        elif p1 < p2:
            return -1

    # 比较beta版本
    if beta1 and not beta2:
        return -1
    elif not beta1 and beta2:
        return 1
    elif beta1 and beta2:
        # beta版本低于正式版本
        return -1

    return 0


def get_current_db_version(db_path: str) -> Optional[str]:
    """获取当前数据库版本

    Args:
        db_path: 数据库文件路径

    Returns:
        版本号，如果无法获取则返回None
    """
    if not os.path.exists(db_path):
        return None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 尝试获取版本信息
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE '%memory_version%'
        """)
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            conn.close()
            return "1.0.0"  # 旧版本没有版本表

        # 获取版本
        cursor.execute(f"SELECT db_version FROM {tables[0]} LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None

    except Exception as e:
        logger.error(f"获取数据库版本失败: {e}")
        return None


class DatabaseMigrator:
    """数据库迁移器"""

    def __init__(self, db_path: str, backup_dir: str):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def backup_database(self) -> str:
        """备份数据库

        Returns:
            备份文件路径
        """
        os.makedirs(self.backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(
            self.backup_dir,
            f"backup_{timestamp}_{os.path.basename(self.db_path)}"
        )

        shutil.copy2(self.db_path, backup_path)
        logger.info(f"数据库已备份到: {backup_path}")

        return backup_path

    def create_version_table_if_not_exists(self):
        """创建版本表（如果不存在）"""
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
        self.conn.commit()

    def insert_version_info_if_empty(self):
        """插入版本信息（如果表为空）"""
        self.cursor.execute("SELECT COUNT(*) FROM qwenpaw_memory_version")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO qwenpaw_memory_version
                (db_version, schema_version, min_compatible_version)
                VALUES ('1.0.0', '1.0.0', '1.0.0')
            """)
            self.conn.commit()

    def add_memory_relations_table(self):
        """添加记忆关联表（v1.0.2-beta0.2+）"""
        try:
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
            logger.info("已创建记忆关联表")
        except Exception as e:
            logger.warning(f"创建记忆关联表失败（可能已存在）: {e}")

    def add_memory_categories_tables(self):
        """添加记忆分类相关表（v1.0.2-beta0.2+）"""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS qwenpaw_memory_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT NOT NULL UNIQUE,
                    category_description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

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
            logger.info("已创建记忆分类相关表")
        except Exception as e:
            logger.warning(f"创建记忆分类表失败（可能已存在）: {e}")

    def add_optimal_indexes(self):
        """添加优化后的索引（v1.0.2-beta0.3+）"""
        indexes = [
            # 复合索引
            "CREATE INDEX IF NOT EXISTS idx_memory_agent_session ON qwenpaw_memory(agent_id, session_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_agent_importance ON qwenpaw_memory(agent_id, importance DESC)",
            "CREATE INDEX IF NOT EXISTS idx_memory_agent_access ON qwenpaw_memory(agent_id, last_accessed_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_memory_agent_frozen ON qwenpaw_memory(agent_id, access_frozen)",

            # 搜索优化索引
            "CREATE INDEX IF NOT EXISTS idx_memory_search ON qwenpaw_memory(agent_id, search_count DESC)",
            "CREATE INDEX IF NOT EXISTS idx_memory_importance_score ON qwenpaw_memory(importance_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_memory_access_count ON qwenpaw_memory(access_count DESC)",

            # 时间范围查询索引
            "CREATE INDEX IF NOT EXISTS idx_memory_time_range ON qwenpaw_memory(created_at, last_accessed_at)",
            "CREATE INDEX IF NOT EXISTS idx_memory_recent ON qwenpaw_memory(last_accessed_at DESC)",

            # 向量表索引
            "CREATE INDEX IF NOT EXISTS idx_vector_type ON qwenpaw_memory_vectors(vector_type)",

            # 缓存表索引
            "CREATE INDEX IF NOT EXISTS idx_cache_hit ON qwenpaw_vector_cache(hit_count DESC)",

            # 工具统计索引
            "CREATE INDEX IF NOT EXISTS idx_tool_stats_calls ON qwenpaw_tool_usage_stats(total_calls DESC)",

            # 记忆关联表索引
            "CREATE INDEX IF NOT EXISTS idx_memory_relations_score ON qwenpaw_memory_relations(similarity_score DESC)",

            # 记忆分类关联表索引
            "CREATE INDEX IF NOT EXISTS idx_memory_category_confidence ON qwenpaw_memory_category_relations(confidence DESC)",
        ]

        for idx_sql in indexes:
            try:
                self.cursor.execute(idx_sql)
            except Exception as e:
                logger.warning(f"创建索引失败: {e}")

        logger.info("已创建优化索引")

    def update_version(self, version: str):
        """更新数据库版本

        Args:
            version: 新版本号
        """
        self.cursor.execute("""
            UPDATE qwenpaw_memory_version
            SET db_version = ?, schema_version = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (version, version))
        self.conn.commit()

    def add_upgrade_record(self, from_version: str, to_version: str, description: str):
        """添加升级记录

        Args:
            from_version: 源版本
            to_version: 目标版本
            description: 升级描述
        """
        self.cursor.execute("""
            SELECT upgrade_history FROM qwenpaw_memory_version LIMIT 1
        """)
        row = self.cursor.fetchone()
        history = json.loads(row[0] or "[]") if row else []

        history.append({
            "from_version": from_version,
            "to_version": to_version,
            "date": datetime.now().isoformat(),
            "description": description
        })

        self.cursor.execute("""
            UPDATE qwenpaw_memory_version
            SET upgrade_history = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (json.dumps(history),))
        self.conn.commit()


def upgrade_from_v1_0_0(migrator: DatabaseMigrator, current_version: str):
    """从v1.0.0升级"""
    logger.info("执行 v1.0.0 升级...")

    migrator.create_version_table_if_not_exists()
    migrator.insert_version_info_if_empty()
    migrator.add_memory_relations_table()
    migrator.add_memory_categories_tables()
    migrator.add_optimal_indexes()

    migrator.update_version("1.0.2-beta0.3")
    migrator.add_upgrade_record(
        current_version,
        "1.0.2-beta0.3",
        "从 v1.0.0 升级到 v1.0.2-beta0.3：添加记忆关联、分类、索引优化"
    )

    return "1.0.2-beta0.3"


def upgrade_from_v1_0_1(migrator: DatabaseMigrator, current_version: str):
    """从v1.0.1升级"""
    logger.info("执行 v1.0.1 升级...")

    migrator.add_memory_relations_table()
    migrator.add_memory_categories_tables()
    migrator.add_optimal_indexes()

    migrator.update_version("1.0.2-beta0.3")
    migrator.add_upgrade_record(
        current_version,
        "1.0.2-beta0.3",
        "从 v1.0.1 升级到 v1.0.2-beta0.3：添加记忆关联、分类、索引优化"
    )

    return "1.0.2-beta0.3"


def upgrade_from_v1_0_2(migrator: DatabaseMigrator, current_version: str):
    """从v1.0.2升级"""
    logger.info("执行 v1.0.2 升级...")

    migrator.add_memory_relations_table()
    migrator.add_memory_categories_tables()
    migrator.add_optimal_indexes()

    migrator.update_version("1.0.2-beta0.3")
    migrator.add_upgrade_record(
        current_version,
        "1.0.2-beta0.3",
        "从 v1.0.2 升级到 v1.0.2-beta0.3：添加记忆关联、分类、索引优化"
    )

    return "1.0.2-beta0.3"


def upgrade_from_beta0_1(migrator: DatabaseMigrator, current_version: str):
    """从v1.0.2-beta0.1升级"""
    logger.info("执行 v1.0.2-beta0.1 升级...")

    migrator.add_memory_relations_table()
    migrator.add_memory_categories_tables()
    migrator.add_optimal_indexes()

    migrator.update_version("1.0.2-beta0.3")
    migrator.add_upgrade_record(
        current_version,
        "1.0.2-beta0.3",
        "从 v1.0.2-beta0.1 升级到 v1.0.2-beta0.3：添加记忆关联、分类、索引优化"
    )

    return "1.0.2-beta0.3"


def upgrade_from_beta0_2(migrator: DatabaseMigrator, current_version: str):
    """从v1.0.2-beta0.2升级"""
    logger.info("执行 v1.0.2-beta0.2 升级...")

    migrator.add_optimal_indexes()

    migrator.update_version("1.0.2-beta0.3")
    migrator.add_upgrade_record(
        current_version,
        "1.0.2-beta0.3",
        "从 v1.0.2-beta0.2 升级到 v1.0.2-beta0.3：索引优化"
    )

    return "1.0.2-beta0.3"


def upgrade_database(db_path: str, backup_dir: str = "./backups") -> bool:
    """升级数据库

    Args:
        db_path: 数据库文件路径
        backup_dir: 备份目录

    Returns:
        是否升级成功
    """
    logger.info("=" * 50)
    logger.info("Human Thinking Memory Manager 统一升级脚本")
    logger.info(f"目标版本: {LATEST_VERSION}")
    logger.info("=" * 50)

    # 检查数据库是否存在
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return False

    # 获取当前版本
    current_version = get_current_db_version(db_path)
    if current_version is None:
        logger.error("无法获取当前数据库版本")
        return False

    logger.info(f"当前数据库版本: {current_version}")

    # 比较版本
    if compare_versions(current_version, LATEST_VERSION) >= 0:
        logger.info("当前数据库版本已是最新，无需升级")
        return True

    # 创建迁移器
    migrator = DatabaseMigrator(db_path, backup_dir)

    try:
        # 连接数据库
        migrator.connect()

        # 备份数据库
        backup_path = migrator.backup_database()

        # 根据当前版本执行升级
        version = current_version
        while compare_versions(version, LATEST_VERSION) < 0:
            if version == "1.0.0":
                version = upgrade_from_v1_0_0(migrator, version)
            elif version == "1.0.1":
                version = upgrade_from_v1_0_1(migrator, version)
            elif version == "1.0.2":
                version = upgrade_from_v1_0_2(migrator, version)
            elif version == "1.0.2-beta0.1":
                version = upgrade_from_beta0_1(migrator, version)
            elif version == "1.0.2-beta0.2":
                version = upgrade_from_beta0_2(migrator, version)
            elif version == "1.0.2-beta0.3":
                logger.info("已是最新版本")
                break
            elif compare_versions(version, "1.0.2") < 0:
                # 1.0.0 到 1.0.2 之间的版本
                version = upgrade_from_v1_0_2(migrator, version)
            else:
                logger.warning(f"未知版本: {version}，跳过")
                break

        migrator.close()

        logger.info("=" * 50)
        logger.info(f"升级完成！")
        logger.info(f"备份文件: {backup_path}")
        logger.info(f"新版本: {version}")
        logger.info("=" * 50)

        return True

    except Exception as e:
        logger.error(f"升级失败: {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Human Thinking Memory Manager 统一升级脚本")
    parser.add_argument(
        "--db-path",
        type=str,
        required=True,
        help="数据库文件路径"
    )
    parser.add_argument(
        "--backup-dir",
        type=str,
        default="./backups",
        help="备份目录（默认: ./backups）"
    )

    args = parser.parse_args()

    success = upgrade_database(args.db_path, args.backup_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
