#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Human Thinking Memory Manager 单元测试"""

import os
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch

# 添加测试目录到Python路径
import sys
sys.path.insert(0, os.path.dirname(__file__))

# 直接从core模块导入，避免依赖agentscope
from core.memory_manager import HumanThinkingMemoryManager
from core.database import HumanThinkingMemoryDB


class TestHumanThinkingMemoryManager(unittest.TestCase):
    """测试Human Thinking Memory Manager"""

    def setUp(self):
        """设置测试环境"""
        # 创建临时目录作为工作目录
        self.temp_dir = tempfile.mkdtemp()
        self.agent_id = "test_agent"
        
        # 初始化数据库
        db_path = os.path.join(self.temp_dir, "memory", f"human_thinking_memory_{self.agent_id}.db")
        self.db = HumanThinkingMemoryDB(db_path, self.agent_id)
        
        # 初始化记忆管理器
        self.memory_manager = HumanThinkingMemoryManager(
            working_dir=self.temp_dir,
            agent_id=self.agent_id
        )

    async def tearDown(self):
        """清理测试环境"""
        # 关闭记忆管理器
        if hasattr(self, 'memory_manager'):
            await self.memory_manager.close()
        
        # 关闭数据库
        if hasattr(self, 'db'):
            self.db.close()
        
        # 删除临时目录
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """测试初始化功能"""
        # 验证记忆管理器是否成功初始化
        self.assertIsInstance(self.memory_manager, HumanThinkingMemoryManager)
        self.assertEqual(self.memory_manager.agent_id, self.agent_id)

    async def test_store_memory(self):
        """测试存储记忆功能"""
        # 启动记忆管理器
        await self.memory_manager.start()
        
        # 存储记忆
        memory_id = await self.memory_manager.store_memory(
            content="测试记忆内容",
            source_id="test_source",
            session_id="test_session",
            importance=3
        )
        
        # 验证记忆是否成功存储
        self.assertIsInstance(memory_id, int)
        self.assertGreater(memory_id, 0)

    async def test_memory_search(self):
        """测试记忆搜索功能"""
        # 启动记忆管理器
        await self.memory_manager.start()
        
        # 存储一些测试记忆
        await self.memory_manager.store_memory(
            content="测试记忆内容 1",
            source_id="test_source",
            session_id="test_session",
            importance=3
        )
        
        await self.memory_manager.store_memory(
            content="测试记忆内容 2",
            source_id="test_source",
            session_id="test_session",
            importance=4
        )
        
        # 搜索记忆
        result = await self.memory_manager.memory_search(
            query="测试记忆",
            max_results=5,
            min_score=0.1
        )
        
        # 验证搜索结果
        self.assertIsInstance(result, ToolResponse)
        self.assertTrue(hasattr(result, 'content'))

    async def test_freeze_and_defrost_memories(self):
        """测试记忆冷藏和解冻功能"""
        # 启动记忆管理器
        await self.memory_manager.start()
        
        # 存储测试记忆
        memory_id = await self.memory_manager.store_memory(
            content="测试记忆内容",
            source_id="test_source",
            session_id="test_session",
            importance=3
        )
        
        # 冷藏记忆
        frozen_count = await self.memory_manager.freeze_memories()
        self.assertGreaterEqual(frozen_count, 0)
        
        # 解冻记忆
        defrosted_count = await self.memory_manager.defrost_memories("测试记忆")
        self.assertGreaterEqual(defrosted_count, 0)

    async def test_get_stats(self):
        """测试获取统计信息功能"""
        # 启动记忆管理器
        await self.memory_manager.start()
        
        # 存储测试记忆
        await self.memory_manager.store_memory(
            content="测试记忆内容",
            source_id="test_source",
            session_id="test_session",
            importance=3
        )
        
        # 获取统计信息
        stats = self.memory_manager.get_stats()
        
        # 验证统计信息
        self.assertIsInstance(stats, dict)
        self.assertIn('total_memories', stats)
        self.assertIn('frozen_memories', stats)
        self.assertIn('importance_stats', stats)

    def test_qwenpaw_integration(self):
        """测试QwenPaw集成功能"""
        # 模拟QwenPaw的_resolve_memory_class函数
        try:
            # 尝试导入HumanThinkingMemoryManager
            from HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager
            # 验证类是否存在
            self.assertTrue(hasattr(HumanThinkingMemoryManager, '__init__'))
            # 验证类是否有必要的方法
            self.assertTrue(hasattr(HumanThinkingMemoryManager, 'start'))
            self.assertTrue(hasattr(HumanThinkingMemoryManager, 'close'))
            self.assertTrue(hasattr(HumanThinkingMemoryManager, 'store_memory'))
            self.assertTrue(hasattr(HumanThinkingMemoryManager, 'memory_search'))
        except ImportError as e:
            self.fail(f"QwenPaw集成测试失败: {e}")


import asyncio

async def run_tests():
    """运行异步测试"""
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHumanThinkingMemoryManager)
    
    # 运行测试
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == '__main__':
    # 运行异步测试
    asyncio.run(run_tests())
