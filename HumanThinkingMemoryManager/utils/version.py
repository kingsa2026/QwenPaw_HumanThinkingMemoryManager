# -*- coding: utf-8 -*-
"""Human Thinking Tool Version Manager"""
import json
from datetime import datetime
from typing import Dict, Any, Optional


class VersionManager:
    """版本管理器"""

    def __init__(self, conn):
        """初始化版本管理器

        Args:
            conn: 数据库连接
        """
        self.conn = conn
        self.cursor = conn.cursor()

    def get_version(self, key: str) -> Optional[str]:
        """获取版本信息

        Args:
            key: 版本键

        Returns:
            Optional[str]: 版本值
        """
        self.cursor.execute(
            "SELECT value FROM human_thinking_memory_version WHERE key = ?",
            (key,)
        )
        row = self.cursor.fetchone()
        if row:
            return row[0]
        return None

    def set_version(self, key: str, value: str, description: Optional[str] = None):
        """设置版本信息

        Args:
            key: 版本键
            value: 版本值
            description: 描述
        """
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO human_thinking_memory_version 
            (key, value, description, updated_at) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (key, value, description)
        )
        self.conn.commit()

    def get_all_versions(self) -> Dict[str, Any]:
        """获取所有版本信息

        Returns:
            Dict[str, Any]: 版本信息
        """
        self.cursor.execute("SELECT key, value, description, updated_at FROM human_thinking_memory_version")
        rows = self.cursor.fetchall()
        versions = {}
        for row in rows:
            versions[row[0]] = {
                "value": row[1],
                "description": row[2],
                "updated_at": row[3]
            }
        return versions

    def need_upgrade(self) -> bool:
        """检查是否需要升级

        Returns:
            bool: 是否需要升级
        """
        current_version = self.get_version("db_version")
        if not current_version:
            return True

        # 比较版本号
        return self._compare_versions(current_version, "1.0.0") < 0

    def upgrade(self, db_path: str):
        """执行升级

        Args:
            db_path: 数据库文件路径
        """
        # 备份旧数据库
        self._backup_database(db_path)

        # 升级数据库结构
        self._upgrade_database()

        # 更新版本信息
        self.set_version("db_version", "1.0.0", "Database structure version")
        self.set_version("schema_version", "1", "Schema version for structure change tracking")
        self.set_version("min_compatible_version", "1.0.0", "Minimum compatible version")
        self.set_version("last_migration_date", datetime.now().isoformat(), "Last migration date")

        # 更新迁移历史
        migration_history = self.get_version("migration_history")
        if migration_history:
            history = json.loads(migration_history)
        else:
            history = []

        history.append({
            "version": "1.0.0",
            "date": datetime.now().isoformat(),
            "description": "Initial database structure"
        })

        self.set_version("migration_history", json.dumps(history), "Migration history in JSON format")

    def _backup_database(self, db_path: str):
        """备份数据库

        Args:
            db_path: 数据库文件路径
        """
        import shutil
        from pathlib import Path
        
        db_path = Path(db_path)
        if db_path.exists():
            # 创建备份目录
            backup_dir = db_path.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成备份文件名
            backup_path = backup_dir / f"{db_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{db_path.suffix}"
            
            # 备份数据库
            shutil.copy2(db_path, backup_path)
            print(f"Backed up database to {backup_path}")

    def _upgrade_database(self):
        """升级数据库结构"""
        # 这里可以添加数据库结构升级逻辑
        # 例如：添加新表、修改表结构等
        pass

    def _compare_versions(self, version1: str, version2: str) -> int:
        """比较版本号

        Args:
            version1: 版本号1
            version2: 版本号2

        Returns:
            int: 1 if version1 > version2, -1 if version1 < version2, 0 otherwise
        """
        v1_parts = list(map(int, version1.split('.')))
        v2_parts = list(map(int, version2.split('.')))

        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1

        if len(v1_parts) > len(v2_parts):
            return 1
        elif len(v1_parts) < len(v2_parts):
            return -1

        return 0

    def get_migration_history(self) -> list:
        """获取迁移历史

        Returns:
            list: 迁移历史
        """
        migration_history = self.get_version("migration_history")
        if migration_history:
            return json.loads(migration_history)
        return []

    def add_migration_record(self, version: str, description: str):
        """添加迁移记录

        Args:
            version: 版本号
            description: 描述
        """
        migration_history = self.get_migration_history()
        migration_history.append({
            "version": version,
            "date": datetime.now().isoformat(),
            "description": description
        })
        self.set_version("migration_history", json.dumps(migration_history), "Migration history in JSON format")
