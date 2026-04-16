#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速验证HumanThinkingMemoryManager功能"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 50)
print("HumanThinkingMemoryManager 快速验证")
print("=" * 50)

try:
    from core.memory_manager import HumanThinkingMemoryManager
    from core.database import HumanThinkingMemoryDB
    from hooks.feishu_message_parser import (
        parse_feishu_content,
        is_important_feishu_message,
        parse_feishu_message
    )
    print("\n✅ 所有模块导入成功")
except Exception as e:
    print(f"\n❌ 模块导入失败: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("1. 测试数据库功能")
print("=" * 50)

temp_dir = tempfile.mkdtemp(prefix="htmm_test_")
try:
    db_path = os.path.join(temp_dir, "test_db.sqlite")
    db = HumanThinkingMemoryDB(db_path, agent_id="test_agent_001")
    print("✅ 数据库初始化成功")

    db.close()
    print("✅ 数据库关闭成功")
finally:
    shutil.rmtree(temp_dir)

print("\n" + "=" * 50)
print("2. 测试飞书消息解析")
print("=" * 50)

test_content = """{
  "title": "项目讨论",
  "content": [
    [
      {"tag": "text", "text": "今天我们讨论了项目计划"},
      {"tag": "at", "user_id": "user123", "user_name": "张三"},
      {"tag": "text", "text": "请查看"}
    ]
  ]
}"""

parsed = parse_feishu_content(test_content)
print(f"✅ 内容解析: {parsed[:100]}...")

msg_info = parse_feishu_message(test_content, message_id="msg123")
print(f"✅ 完整解析成功")

is_important = is_important_feishu_message(test_content)
print(f"✅ 重要性判断: {'是' if is_important else '否'}")

print("\n" + "=" * 50)
print("3. 测试记忆管理器初始化")
print("=" * 50)

temp_working_dir = tempfile.mkdtemp(prefix="htmm_working_")
try:
    manager = HumanThinkingMemoryManager(
        working_dir=temp_working_dir,
        agent_id="test_agent_001"
    )
    print("✅ 记忆管理器初始化成功")
    print(f"   - Agent ID: {manager.agent_id}")
    print(f"   - 工作目录: {manager.working_dir}")

finally:
    shutil.rmtree(temp_working_dir)

print("\n" + "=" * 50)
print("✅ 所有验证通过！")
print("=" * 50)
