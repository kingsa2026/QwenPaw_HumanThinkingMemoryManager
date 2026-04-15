# -*- coding: utf-8 -*-
"""Human Thinking Tool Memory Migrator"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class MemoryMigrator:
    """记忆数据迁移器"""

    def __init__(self, workspace_dir: str, agent_id: str, db):
        """初始化迁移器

        Args:
            workspace_dir: 工作目录路径
            agent_id: Agent ID
            db: 数据库实例
        """
        self.workspace_dir = workspace_dir
        self.agent_id = agent_id
        self.db = db

        # 迁移历史文件
        self.migration_history_path = Path(workspace_dir) / "memory" / "migration_history.json"
        self.migration_history = self._load_migration_history()

    def _load_migration_history(self) -> Dict[str, Any]:
        """加载迁移历史

        Returns:
            Dict[str, Any]: 迁移历史
        """
        if self.migration_history_path.exists():
            try:
                with open(self.migration_history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading migration history: {e}")
                return {}
        return {}

    def _save_migration_history(self):
        """保存迁移历史"""
        try:
            self.migration_history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.migration_history_path, 'w', encoding='utf-8') as f:
                json.dump(self.migration_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving migration history: {e}")

    async def migrate_if_needed(self) -> bool:
        """检查并执行迁移

        Returns:
            bool: 是否执行了迁移
        """
        # 检查是否需要迁移
        if not self._needs_migration():
            return False

        # 执行迁移
        try:
            await self._migrate()
            # 更新迁移历史
            self._update_migration_history()
            return True
        except Exception as e:
            print(f"Error during migration: {e}")
            return False

    def _needs_migration(self) -> bool:
        """检查是否需要迁移

        Returns:
            bool: 是否需要迁移
        """
        # 检查是否存在旧的记忆文件
        old_memory_path = Path(self.workspace_dir) / "memory" / "MEMORY.md"
        old_json_path = Path(self.workspace_dir) / "memory" / "memory.json"
        
        if old_memory_path.exists() or old_json_path.exists():
            # 检查是否已经迁移过
            migration_key = f"migrated_{self.agent_id}"
            return not self.migration_history.get(migration_key, False)
        return False

    async def _migrate(self):
        """执行迁移"""
        # 迁移旧的 MEMORY.md 文件
        old_memory_path = Path(self.workspace_dir) / "memory" / "MEMORY.md"
        if old_memory_path.exists():
            await self._migrate_from_memory_md(old_memory_path)

        # 迁移其他可能的旧格式
        # 例如：JSON格式的记忆文件
        old_json_path = Path(self.workspace_dir) / "memory" / "memory.json"
        if old_json_path.exists():
            await self._migrate_from_json(old_json_path)

    async def _migrate_from_memory_md(self, file_path: Path):
        """从 MEMORY.md 文件迁移

        Args:
            file_path: 文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析 MEMORY.md 格式
            # 假设格式为：
            # - [timestamp] content
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and line.startswith('- ['):
                    # 提取时间戳和内容
                    timestamp_part = line[2:line.find(']')]
                    content_part = line[line.find(']')+1:].strip()

                    try:
                        # 尝试解析时间戳
                        timestamp = datetime.fromisoformat(timestamp_part)
                        # 存储到新数据库
                        await self.db.store_memory(
                            content=content_part,
                            source_id="migration",
                            session_id=self.agent_id,
                            importance=3
                        )
                    except Exception as e:
                        print(f"Error parsing line: {line}")
                        print(f"Error: {e}")

            print(f"Migrated {len(lines)} lines from MEMORY.md")
        except Exception as e:
            print(f"Error migrating from MEMORY.md: {e}")

    async def _migrate_from_json(self, file_path: Path):
        """从 JSON 文件迁移

        Args:
            file_path: 文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 假设 JSON 格式为：
            # [
            #   {"content": "...", "timestamp": "...", "importance": 3},
            #   ...
            # ]
            if isinstance(data, list):
                for item in data:
                    content = item.get("content", "")
                    importance = item.get("importance", 3)
                    if content:
                        await self.db.store_memory(
                            content=content,
                            source_id="migration",
                            session_id=self.agent_id,
                            importance=importance
                        )

                print(f"Migrated {len(data)} items from memory.json")
        except Exception as e:
            print(f"Error migrating from memory.json: {e}")

    def _update_migration_history(self):
        """更新迁移历史"""
        migration_key = f"migrated_{self.agent_id}"
        self.migration_history[migration_key] = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "workspace_dir": self.workspace_dir
        }
        self._save_migration_history()

    def backup_old_files(self):
        """备份旧文件"""
        backup_dir = Path(self.workspace_dir) / "memory" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 备份 MEMORY.md
        old_memory_path = Path(self.workspace_dir) / "memory" / "MEMORY.md"
        if old_memory_path.exists():
            backup_path = backup_dir / f"MEMORY.md.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(old_memory_path, backup_path)
            print(f"Backed up MEMORY.md to {backup_path}")

        # 备份 memory.json
        old_json_path = Path(self.workspace_dir) / "memory" / "memory.json"
        if old_json_path.exists():
            backup_path = backup_dir / f"memory.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(old_json_path, backup_path)
            print(f"Backed up memory.json to {backup_path}")

    def cleanup_old_files(self):
        """清理旧文件"""
        # 清理 MEMORY.md
        old_memory_path = Path(self.workspace_dir) / "memory" / "MEMORY.md"
        if old_memory_path.exists():
            old_memory_path.unlink()
            print(f"Removed old MEMORY.md")

        # 清理 memory.json
        old_json_path = Path(self.workspace_dir) / "memory" / "memory.json"
        if old_json_path.exists():
            old_json_path.unlink()
            print(f"Removed old memory.json")
