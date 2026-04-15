#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试会话管理和缓存机制"""
import asyncio
import time
from HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager

async def test_session_management():
    """测试会话管理功能"""
    print("=== 测试会话管理 ===")
    
    # 创建两个不同的agent
    agent1 = HumanThinkingMemoryManager(
        working_dir="./test_agent1",
        agent_id="test_agent_1"
    )
    agent2 = HumanThinkingMemoryManager(
        working_dir="./test_agent2",
        agent_id="test_agent_2"
    )
    
    # 启动内存管理器
    await agent1.start()
    await agent2.start()
    
    try:
        # 测试1: 为agent1创建两个不同的会话
        print("\n1. 为agent1创建两个不同的会话")
        session1 = "session_1"
        session2 = "session_2"
        
        # 向session1添加记忆
        for i in range(3):
            await agent1.store_memory(
                content=f"Agent1 Session1 记忆{i}",
                source_id="user",
                session_id=session1
            )
        
        # 向session2添加记忆
        for i in range(3):
            await agent2.store_memory(
                content=f"Agent2 Session2 记忆{i}",
                source_id="user",
                session_id=session2
            )
        
        # 测试2: 验证搜索时会话过滤
        print("\n2. 验证搜索时会话过滤")
        # 从agent1的session1搜索
        result1 = await agent1.memory_search(
            query="记忆",
            session_id=session1
        )
        print(f"Agent1 Session1 搜索结果: {len(result1.content)}条")
        for block in result1.content:
            print(f"  - {block.text}")
        
        # 从agent2的session2搜索
        result2 = await agent2.memory_search(
            query="记忆",
            session_id=session2
        )
        print(f"\nAgent2 Session2 搜索结果: {len(result2.content)}条")
        for block in result2.content:
            print(f"  - {block.text}")
        
        # 测试3: 验证缓存机制
        print("\n3. 验证缓存机制")
        # 向agent1添加更多记忆，触发缓存批量写入
        for i in range(8):  # 加上之前的3条，共11条，超过batch_threshold=10
            await agent1.store_memory(
                content=f"Agent1 Session1 缓存测试记忆{i}",
                source_id="user",
                session_id=session1
            )
        print("添加了8条记忆，应该触发缓存批量写入")
        
        # 测试4: 验证跨agent隔离
        print("\n4. 验证跨agent隔离")
        # 从agent1搜索agent2的内容
        result3 = await agent1.memory_search(
            query="Agent2"
        )
        print(f"Agent1搜索'Agent2'的结果: {len(result3.content)}条")
        for block in result3.content:
            print(f"  - {block.text}")
        
        # 测试5: 验证会话超时清理
        print("\n5. 验证会话超时清理")
        # 获取当前会话数量
        initial_count = agent1.session_manager.get_session_count("test_agent_1")
        print(f"初始会话数量: {initial_count}")
        
        # 模拟会话超时
        print("等待6秒模拟会话超时...")
        time.sleep(6)
        
        # 清理超时会话（设置为5秒超时）
        agent1.session_manager.cleanup_sessions(timeout=5)
        
        # 检查清理后的会话数量
        final_count = agent1.session_manager.get_session_count("test_agent_1")
        print(f"清理后会话数量: {final_count}")
        
    finally:
        # 关闭内存管理器
        await agent1.close()
        await agent2.close()
        print("\n测试完成，内存管理器已关闭")

if __name__ == "__main__":
    asyncio.run(test_session_management())
