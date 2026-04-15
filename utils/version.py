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
            "SELECT db_version FROM qwenpaw_memory_version LIMIT 1",
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
        # 版本信息已经在数据库初始化时插入
        pass

    def get_all_versions(self) -> Dict[str, Any]:
        """获取所有版本信息

        Returns:
            Dict[str, Any]: 版本信息
        """
        self.cursor.execute("SELECT db_version, schema_version, min_compatible_version, created_at, updated_at, upgrade_history FROM qwenpaw_memory_version LIMIT 1")
        row = self.cursor.fetchone()
        if row:
            return {
                "db_version": row[0],
                "schema_version": row[1],
                "min_compatible_version": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "upgrade_history": row[5]
            }
        return {}

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

        # 版本信息已经在数据库初始化时插入，这里只需要更新版本号
        self.cursor.execute(
            """
            UPDATE qwenpaw_memory_version 
            SET db_version = ?, schema_version = ?, 
                min_compatible_version = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            ("1.0.2 bata0.1", "1.0.2 bata0.1", "1.0.0")
        )
        self.conn.commit()

        print(f"Database upgraded to version 1.0.2 bata0.1")

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
        self.cursor.execute("SELECT upgrade_history FROM qwenpaw_memory_version LIMIT 1")
        row = self.cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return []

    def add_migration_record(self, version: str, description: str):
        """添加迁移记录

        Args:
            version: 版本号
            description: 描述
        """
        # 获取当前迁移历史
        history = self.get_migration_history()
        
        # 添加新记录
        history.append({
            "version": version,
            "date": datetime.now().isoformat(),
            "description": description
        })
        
        # 更新数据库
        self.cursor.execute(
            """
            UPDATE qwenpaw_memory_version 
            SET upgrade_history = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (json.dumps(history),)
        )
        self.conn.commit()
