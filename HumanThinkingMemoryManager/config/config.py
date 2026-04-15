# -*- coding: utf-8 -*-
"""Human Thinking Tool Config Module"""
import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置加载器

        Args:
            config_dir: 配置目录路径
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 默认配置目录
            self.config_dir = Path(os.path.expanduser("~")) / ".qwenpaw" / "config"
        
        self.config_file = self.config_dir / "human_thinking_tool.yaml"
        self.default_config = self._get_default_config()
        self.config = self._load_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置

        Returns:
            Dict[str, Any]: 默认配置
        """
        return {
            "memory": {
                "db_path": "memory/human_thinking_memory.db",
                "vector_enabled": True,
                "vector_dimension": 384,
                "vector_type": "text-embedding-3-small",
                "model_name": "openai"
            },
            "search": {
                "max_results": 5,
                "min_score": 0.1,
                "cache_enabled": True,
                "cache_ttl": 3600
            },
            "backup": {
                "enabled": True,
                "max_backups": 5,
                "backup_dir": "backups"
            },
            "freezer": {
                "enabled": True,
                "days_threshold": 30,
                "importance_threshold": 4
            },
            "monitoring": {
                "enabled": True,
                "metrics_enabled": True,
                "logs_enabled": True
            },
            "migration": {
                "enabled": True,
                "backup_old_files": True,
                "cleanup_old_files": True
            }
        }

    def _load_config(self) -> Dict[str, Any]:
        """加载配置

        Returns:
            Dict[str, Any]: 配置
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                if config:
                    # 合并默认配置和用户配置
                    return self._merge_configs(self.default_config, config)
            except Exception as e:
                print(f"Error loading config: {e}")
        return self.default_config

    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置

        Args:
            default: 默认配置
            user: 用户配置

        Returns:
            Dict[str, Any]: 合并后的配置
        """
        merged = default.copy()
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """保存配置

        Args:
            config: 要保存的配置
        """
        if config:
            self.config = config
        
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键（支持点号分隔，如 "memory.vector_enabled"）
            default: 默认值

        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置值

        Args:
            key: 配置键（支持点号分隔，如 "memory.vector_enabled"）
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        for i, k in enumerate(keys):
            if i == len(keys) - 1:
                config[k] = value
            else:
                if k not in config:
                    config[k] = {}
                config = config[k]

    def validate_config(self) -> bool:
        """验证配置

        Returns:
            bool: 配置是否有效
        """
        # 验证必要的配置项
        required_keys = [
            "memory.db_path",
            "memory.vector_enabled",
            "search.max_results",
            "backup.enabled"
        ]

        for key in required_keys:
            if self.get(key) is None:
                print(f"Missing required config: {key}")
                return False

        # 验证配置值的类型
        type_checks = [
            ("memory.vector_enabled", bool),
            ("search.max_results", int),
            ("search.min_score", float),
            ("backup.enabled", bool),
            ("freezer.enabled", bool),
            ("freezer.days_threshold", int),
            ("freezer.importance_threshold", int),
            ("monitoring.enabled", bool),
            ("migration.enabled", bool)
        ]

        for key, expected_type in type_checks:
            value = self.get(key)
            if value is not None and not isinstance(value, expected_type):
                print(f"Invalid type for {key}: expected {expected_type}, got {type(value)}")
                return False

        return True

    def get_full_config(self) -> Dict[str, Any]:
        """获取完整配置

        Returns:
            Dict[str, Any]: 完整配置
        """
        return self.config

    def reload_config(self):
        """重新加载配置"""
        self.config = self._load_config()

    def export_config(self, format: str = "yaml") -> str:
        """导出配置

        Args:
            format: 格式（yaml 或 json）

        Returns:
            str: 导出的配置
        """
        if format == "json":
            return json.dumps(self.config, ensure_ascii=False, indent=2)
        else:
            return yaml.dump(self.config, allow_unicode=True, default_flow_style=False)

    def import_config(self, config_str: str, format: str = "yaml"):
        """导入配置

        Args:
            config_str: 配置字符串
            format: 格式（yaml 或 json）
        """
        try:
            if format == "json":
                config = json.loads(config_str)
            else:
                config = yaml.safe_load(config_str)
            if config:
                self.config = self._merge_configs(self.default_config, config)
                self.save_config()
        except Exception as e:
            print(f"Error importing config: {e}")
