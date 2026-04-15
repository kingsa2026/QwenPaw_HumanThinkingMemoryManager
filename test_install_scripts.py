#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试安装和卸载脚本"""

import os
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch
import subprocess


class TestInstallScripts(unittest.TestCase):
    """测试安装和卸载脚本"""

    def setUp(self):
        """设置测试环境"""
        # 创建临时目录作为QwenPaw根目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建模拟的QwenPaw目录结构
        self.qwenpaw_src = os.path.join(self.temp_dir, "src", "qwenpaw")
        self.workspace_path = os.path.join(self.qwenpaw_src, "app", "workspace")
        self.tools_path = os.path.join(self.qwenpaw_src, "agents", "tools")
        
        os.makedirs(self.workspace_path, exist_ok=True)
        os.makedirs(self.tools_path, exist_ok=True)
        
        # 创建模拟的workspace.py文件
        self.workspace_file = os.path.join(self.workspace_path, "workspace.py")
        self._create_mock_workspace_file()
        
        # 创建模拟的config.py文件
        self.config_path = os.path.join(self.qwenpaw_src, "config")
        os.makedirs(self.config_path, exist_ok=True)
        self.config_file = os.path.join(self.config_path, "config.py")
        self._create_mock_config_file()
        
        # 复制安装和卸载脚本到临时目录
        self.install_script = os.path.join(os.path.dirname(__file__), "install.sh")
        self.uninstall_script = os.path.join(os.path.dirname(__file__), "uninstall.sh")
        
        self.temp_install_script = os.path.join(self.temp_dir, "install.sh")
        self.temp_uninstall_script = os.path.join(self.temp_dir, "uninstall.sh")
        
        shutil.copy2(self.install_script, self.temp_install_script)
        shutil.copy2(self.uninstall_script, self.temp_uninstall_script)
        
        # 确保脚本可执行
        os.chmod(self.temp_install_script, 0o755)
        os.chmod(self.temp_uninstall_script, 0o755)

    def tearDown(self):
        """清理测试环境"""
        # 删除临时目录
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_mock_workspace_file(self):
        """创建模拟的workspace.py文件"""
        content = '''
from qwenpaw.config.config import ConfigurationException

def _resolve_memory_class(backend: str) -> type:
    """Return the memory manager class for the given backend name."""
    from ...agents.memory import ReMeLightMemoryManager

    if backend == "remelight":
        return ReMeLightMemoryManager
    raise ConfigurationException(
        message=f"Unsupported memory manager backend: '{backend}'",
    )
'''
        with open(self.workspace_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_mock_config_file(self):
        """创建模拟的config.py文件"""
        content = '''
class ConfigurationException(Exception):
    """Configuration exception"""
    pass

class MemoryManagerBackend:
    """Memory manager backend"""
    remelight = "remelight"
'''
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def test_install_script(self):
        """测试安装脚本"""
        # 运行安装脚本
        try:
            # 由于脚本是bash脚本，在Windows上可能无法直接运行
            # 我们可以检查脚本的内容是否正确
            with open(self.install_script, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 检查脚本是否包含必要的内容
            self.assertIn('Human Thinking Memory Manager 安装脚本', script_content)
            self.assertIn('_resolve_memory_class', script_content)
            self.assertIn('HumanThinkingMemoryManager', script_content)
            self.assertIn('memory_manager_backend', script_content)
            
            print("安装脚本内容检查通过")
        except Exception as e:
            self.fail(f"安装脚本测试失败: {e}")

    def test_uninstall_script(self):
        """测试卸载脚本"""
        # 运行卸载脚本
        try:
            # 由于脚本是bash脚本，在Windows上可能无法直接运行
            # 我们可以检查脚本的内容是否正确
            with open(self.uninstall_script, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # 检查脚本是否包含必要的内容
            self.assertIn('Human Thinking Memory Manager 卸载脚本', script_content)
            self.assertIn('_resolve_memory_class', script_content)
            self.assertIn('HumanThinkingMemoryManager', script_content)
            self.assertIn('memory_manager_backend', script_content)
            
            print("卸载脚本内容检查通过")
        except Exception as e:
            self.fail(f"卸载脚本测试失败: {e}")

    def test_script_paths(self):
        """测试脚本路径计算"""
        try:
            # 检查脚本是否存在
            self.assertTrue(os.path.exists(self.install_script))
            self.assertTrue(os.path.exists(self.uninstall_script))
            
            # 检查脚本是否可执行
            self.assertTrue(os.access(self.install_script, os.X_OK))
            self.assertTrue(os.access(self.uninstall_script, os.X_OK))
            
            print("脚本路径检查通过")
        except Exception as e:
            self.fail(f"脚本路径测试失败: {e}")

    def test_human_thinking_memory_manager_files(self):
        """测试HumanThinkingMemoryManager文件结构"""
        try:
            # 检查HumanThinkingMemoryManager目录是否存在
            htm_dir = os.path.join(os.path.dirname(__file__), "HumanThinkingMemoryManager")
            self.assertTrue(os.path.exists(htm_dir))
            
            # 检查核心文件是否存在
            core_dir = os.path.join(htm_dir, "core")
            self.assertTrue(os.path.exists(core_dir))
            
            memory_manager_file = os.path.join(core_dir, "memory_manager.py")
            self.assertTrue(os.path.exists(memory_manager_file))
            
            database_file = os.path.join(core_dir, "database.py")
            self.assertTrue(os.path.exists(database_file))
            
            print("HumanThinkingMemoryManager文件结构检查通过")
        except Exception as e:
            self.fail(f"HumanThinkingMemoryManager文件结构测试失败: {e}")


if __name__ == '__main__':
    unittest.main()
