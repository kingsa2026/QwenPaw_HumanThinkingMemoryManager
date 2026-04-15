# -*- coding: utf-8 -*-
"""Human Thinking Tool - Super Neural Memory System"""
import os
import json
import sqlite3
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 只导入核心模块，避免依赖agentscope
from .core.memory_manager import HumanThinkingMemoryManager
from .config.config import ConfigLoader

# 模拟ToolBase和ToolResponse类，避免依赖agentscope
class ToolParam:
    """模拟ToolParam类"""
    def __init__(self, name, type, description, required=False, enum=None):
        self.name = name
        self.type = type
        self.description = description
        self.required = required
        self.enum = enum

class ToolResponse:
    """模拟ToolResponse类"""
    def __init__(self, content):
        self.content = content

class ToolBase:
    """模拟ToolBase类"""
    def __init__(self):
        pass


class HumanThinkingTool(ToolBase):
    """Human Thinking Tool - Super Neural Memory System"""

    def __init__(self):
        """Initialize Human Thinking Tool"""
        super().__init__()
        self.name = "human_thinking"
        self.description = "超级神经记忆系统+跨session碎片化记忆整合+神经元感知向量记忆检索架构"
        self.parameters = [
            ToolParam(
                name="action",
                type="string",
                description="操作类型：enable（启用工具）、disable（禁用工具）、backup（备份工作空间）、search（搜索记忆）、store（存储记忆）、stats（查看统计信息）",
                required=True,
                enum=["enable", "disable", "backup", "search", "store", "stats"]
            ),
            ToolParam(
                name="query",
                type="string",
                description="搜索记忆的查询关键词（仅在action为search时使用）",
                required=False
            ),
            ToolParam(
                name="content",
                type="string",
                description="存储记忆的内容（仅在action为store时使用）",
                required=False
            ),
            ToolParam(
                name="importance",
                type="integer",
                description="记忆的重要性等级（1-5，仅在action为store时使用）",
                required=False
            ),
            ToolParam(
                name="agent_id",
                type="string",
                description="Agent ID（可选）",
                required=False
            )
        ]

    async def _run(self, **kwargs) -> ToolResponse:
        """Run Human Thinking Tool"""
        action = kwargs.get("action")
        query = kwargs.get("query")
        content = kwargs.get("content")
        importance = kwargs.get("importance", 3)
        agent_id = kwargs.get("agent_id")

        if action == "enable":
            return await self._enable_tool()
        elif action == "disable":
            return await self._disable_tool()
        elif action == "backup":
            return await self._backup_workspace()
        elif action == "search":
            if not query:
                return ToolResponse(
                    content=[{"type": "text", "text": "错误：搜索操作需要提供query参数"}]
                )
            return await self._search_memory(query, agent_id)
        elif action == "store":
            if not content:
                return ToolResponse(
                    content=[{"type": "text", "text": "错误：存储操作需要提供content参数"}]
                )
            return await self._store_memory(content, importance, agent_id)
        elif action == "stats":
            return await self._get_stats(agent_id)
        else:
            return ToolResponse(
                content=[{"type": "text", "text": f"错误：不支持的操作类型：{action}"}]
            )

    async def _enable_tool(self) -> ToolResponse:
        """Enable Human Thinking Tool"""
        try:
            # Step 1: Backup all agent workspaces
            backup_result = await self._backup_workspace()
            if "错误" in backup_result.content[0]["text"]:
                return backup_result

            # Step 2: Scan agent list, agent IDs, and workspace addresses
            agents = self._scan_agent_workspaces()
            if not agents:
                return ToolResponse(
                    content=[{"type": "text", "text": "警告：未找到agent工作空间，继续安装"}]
                )

            # Step 3: Create memory manager for each agent
            for agent in agents:
                await self._initialize_memory_manager(agent)

            # Step 4: Install enhanced memory manager
            self._install_enhanced_memory_manager()

            # Step 5: Restart QwenPaw service
            self._restart_service()

            return ToolResponse(
                content=[{"type": "text", "text": "Human Thinking工具启用成功！"}]
            )
        except Exception as e:
            return ToolResponse(
                content=[{"type": "text", "text": f"错误：启用工具失败 - {str(e)}"}]
            )

    async def _disable_tool(self) -> ToolResponse:
        """Disable Human Thinking Tool"""
        try:
            # Step 1: Backup all agent workspaces
            backup_result = await self._backup_workspace()
            if "错误" in backup_result.content[0]["text"]:
                return backup_result

            # Step 2: Restore modified files
            self._restore_files()

            # Step 3: Restart QwenPaw service
            self._restart_service()

            return ToolResponse(
                content=[{"type": "text", "text": "Human Thinking工具禁用成功！"}]
            )
        except Exception as e:
            return ToolResponse(
                content=[{"type": "text", "text": f"错误：禁用工具失败 - {str(e)}"}]
            )

    async def _backup_workspace(self) -> ToolResponse:
        """Backup all agent workspaces"""
        try:
            backup_dir = os.path.join(os.path.dirname(__file__), "../../../backups")
            os.makedirs(backup_dir, exist_ok=True)

            agents = self._scan_agent_workspaces()
            success_count = 0

            for agent in agents:
                agent_id = agent.get("agent_id")
                workspace_path = agent.get("workspace_path")

                if not agent_id or not workspace_path:
                    continue

                # Create backup filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"{agent_id}_backup_{timestamp}.zip"
                backup_path = os.path.join(backup_dir, backup_filename)

                # Create zip backup
                import zipfile
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # Add all files in workspace
                    for root, dirs, files in os.walk(workspace_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, workspace_path)
                            zf.write(file_path, arcname)
                    
                    # Add backup info
                    backup_info = {
                        "agent_id": agent_id,
                        "backup_time": datetime.now().isoformat(),
                        "workspace_path": workspace_path
                    }
                    zf.writestr("backup_info.json", json.dumps(backup_info, ensure_ascii=False, indent=2))

                success_count += 1

            # Clean up old backups
            self._cleanup_old_backups(backup_dir)

            return ToolResponse(
                content=[{"type": "text", "text": f"备份完成：成功备份 {success_count} 个agent工作空间"}]
            )
        except Exception as e:
            return ToolResponse(
                content=[{"type": "text", "text": f"错误：备份失败 - {str(e)}"}]
            )

    async def _search_memory(self, query: str, agent_id: Optional[str] = None) -> ToolResponse:
        """Search memory"""
        try:
            agents = self._scan_agent_workspaces()
            results = []

            for agent in agents:
                if agent_id and agent.get("agent_id") != agent_id:
                    continue

                agent_id = agent.get("agent_id")
                workspace_path = agent.get("workspace_path")

                if not agent_id or not workspace_path:
                    continue

                # Initialize memory manager
                memory_manager = HumanThinkingMemoryManager(
                    working_dir=workspace_path,
                    agent_id=agent_id
                )

                # Start memory manager
                await memory_manager.start()

                # Search memory
                search_result = await memory_manager.memory_search(query)
                if search_result.content:
                    results.append(f"Agent {agent_id} 的记忆：")
                    for item in search_result.content:
                        results.append(item.text)
                    results.append("")

                # Close memory manager
                await memory_manager.close()

            if not results:
                return ToolResponse(
                    content=[{"type": "text", "text": "未找到相关记忆"}]
                )

            return ToolResponse(
                content=[{"type": "text", "text": "\n".join(results)}]
            )
        except Exception as e:
            return ToolResponse(
                content=[{"type": "text", "text": f"错误：搜索记忆失败 - {str(e)}"}]
            )

    async def _store_memory(self, content: str, importance: int, agent_id: Optional[str] = None) -> ToolResponse:
        """Store memory"""
        try:
            agents = self._scan_agent_workspaces()
            stored_count = 0

            for agent in agents:
                if agent_id and agent.get("agent_id") != agent_id:
                    continue

                agent_id = agent.get("agent_id")
                workspace_path = agent.get("workspace_path")

                if not agent_id or not workspace_path:
                    continue

                # Initialize memory manager
                memory_manager = HumanThinkingMemoryManager(
                    working_dir=workspace_path,
                    agent_id=agent_id
                )

                # Start memory manager
                await memory_manager.start()

                # Store memory
                memory_id = await memory_manager.store_memory(
                    content=content,
                    importance=importance
                )
                stored_count += 1

                # Close memory manager
                await memory_manager.close()

            if stored_count == 0:
                return ToolResponse(
                    content=[{"type": "text", "text": "未找到可存储的agent工作空间"}]
                )

            return ToolResponse(
                content=[{"type": "text", "text": f"成功存储记忆到 {stored_count} 个agent工作空间"}]
            )
        except Exception as e:
            return ToolResponse(
                content=[{"type": "text", "text": f"错误：存储记忆失败 - {str(e)}"}]
            )

    async def _get_stats(self, agent_id: Optional[str] = None) -> ToolResponse:
        """Get memory stats"""
        try:
            agents = self._scan_agent_workspaces()
            stats = []

            for agent in agents:
                if agent_id and agent.get("agent_id") != agent_id:
                    continue

                agent_id = agent.get("agent_id")
                workspace_path = agent.get("workspace_path")

                if not agent_id or not workspace_path:
                    continue

                # Initialize memory manager
                memory_manager = HumanThinkingMemoryManager(
                    working_dir=workspace_path,
                    agent_id=agent_id
                )

                # Start memory manager
                await memory_manager.start()

                # Get stats
                agent_stats = memory_manager.get_stats()
                stats.append(f"Agent {agent_id} 的统计信息：")
                stats.append(f"  总记忆数：{agent_stats.get('total_memories', 0)}")
                stats.append(f"  冷藏记忆数：{agent_stats.get('frozen_memories', 0)}")
                stats.append(f"  重要性分布：{agent_stats.get('importance_stats', {})}")
                stats.append(f"  最后更新：{agent_stats.get('last_updated', 'N/A')}")
                stats.append("")

                # Close memory manager
                await memory_manager.close()

            if not stats:
                return ToolResponse(
                    content=[{"type": "text", "text": "未找到可统计的agent工作空间"}]
                )

            return ToolResponse(
                content=[{"type": "text", "text": "\n".join(stats)}]
            )
        except Exception as e:
            return ToolResponse(
                content=[{"type": "text", "text": f"错误：获取统计信息失败 - {str(e)}"}]
            )

    async def _initialize_memory_manager(self, agent: Dict[str, Any]):
        """Initialize memory manager for agent"""
        agent_id = agent.get("agent_id")
        workspace_path = agent.get("workspace_path")

        if not agent_id or not workspace_path:
            return

        # Initialize memory manager
        memory_manager = HumanThinkingMemoryManager(
            working_dir=workspace_path,
            agent_id=agent_id
        )

        # Start memory manager
        await memory_manager.start()

        # Close memory manager
        await memory_manager.close()

    def _scan_agent_workspaces(self) -> List[Dict[str, Any]]:
        """Scan agent workspaces"""
        workspaces = []
        qwenpaw_path = os.path.join(os.path.dirname(__file__), "../../../..")

        possible_workspaces = [
            os.path.join(os.path.expanduser("~"), ".qwenpaw", "workspaces"),
            os.path.join(qwenpaw_path, "workspaces")
        ]

        for ws_dir in possible_workspaces:
            if os.path.exists(ws_dir):
                for agent_dir in os.listdir(ws_dir):
                    agent_path = os.path.join(ws_dir, agent_dir)
                    if os.path.isdir(agent_path):
                        workspaces.append({
                            "agent_id": agent_dir,
                            "workspace_path": agent_path
                        })

        return workspaces

    def _install_enhanced_memory_manager(self):
        """Install enhanced memory manager"""
        # Modify workspace.py to use enhanced memory manager
        workspace_path = os.path.join(os.path.dirname(__file__), "../../../app/workspace/workspace.py")
        
        if os.path.exists(workspace_path):
            with open(workspace_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add import for HumanThinkingMemoryManager
            if "HumanThinkingMemoryManager" not in content:
                import_pattern = r"from \.\.\.agents\.memory import ReMeLightMemoryManager"
                import_replacement = "from ...agents.memory import ReMeLightMemoryManager\nfrom ...agents.tools.human_thinking_tool.core.memory_manager import HumanThinkingMemoryManager"
                content = import_pattern.sub(import_replacement, content)

                # Modify _resolve_memory_class function
                resolve_memory_pattern = r"def _resolve_memory_class\(backend: str\) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from \.\.\.agents\.memory import ReMeLightMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    raise ConfigurationException\(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    \)"
                resolve_memory_replacement = "def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n    from ...agents.tools.human_thinking_tool.core.memory_manager import HumanThinkingMemoryManager\n\n    if backend == \"remelight\":\n        return HumanThinkingMemoryManager\n    raise ConfigurationException\(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    \)"
                content = resolve_memory_pattern.sub(resolve_memory_replacement, content)

                with open(workspace_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def _restore_files(self):
        """Restore modified files"""
        # Restore workspace.py
        workspace_path = os.path.join(os.path.dirname(__file__), "../../../app/workspace/workspace.py")
        
        if os.path.exists(workspace_path):
            with open(workspace_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Restore import
            if "HumanThinkingMemoryManager" in content:
                import_pattern = r"from \.\.\.agents\.memory import ReMeLightMemoryManager\nfrom \.\.\.agents\.tools\.human_thinking_tool\.core\.memory_manager import HumanThinkingMemoryManager"
                import_replacement = "from ...agents.memory import ReMeLightMemoryManager"
                content = import_pattern.sub(import_replacement, content)

                # Restore _resolve_memory_class function
                resolve_memory_pattern = r"def _resolve_memory_class\(backend: str\) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from \.\.\.agents\.memory import ReMeLightMemoryManager\n    from \.\.\.agents\.tools\.human_thinking_tool\.core\.memory_manager import HumanThinkingMemoryManager\n\n    if backend == \"remelight\":\n        return HumanThinkingMemoryManager\n    raise ConfigurationException\(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    \)"
                resolve_memory_replacement = "def _resolve_memory_class(backend: str) -> type:\n    \"\"\"Return the memory manager class for the given backend name.\"\"\"\n    from ...agents.memory import ReMeLightMemoryManager\n\n    if backend == \"remelight\":\n        return ReMeLightMemoryManager\n    raise ConfigurationException\(\n        message=f\"Unsupported memory manager backend: '{backend}'\"\,\n    \)"
                content = resolve_memory_pattern.sub(resolve_memory_replacement, content)

                with open(workspace_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def _restart_service(self):
        """Restart QwenPaw service"""
        # Try different methods to restart the service
        methods = [
            # Method 1: Using taskkill for Windows
            ["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq QwenPaw"],
            # Method 2: Using taskkill with process name
            ["taskkill", "/F", "/IM", "python.exe", "/FI", "COMMANDLINE eq *qwenpaw*"]
        ]

        for method in methods:
            try:
                import subprocess
                subprocess.run(method, capture_output=True, text=True)
            except Exception as e:
                pass

        # Start service
        qwenpaw_path = os.path.join(os.path.dirname(__file__), "../../../..")
        try:
            import subprocess
            if os.name == 'nt':  # Windows
                subprocess.Popen(
                    ["python", "-m", "qwenpaw"],
                    cwd=qwenpaw_path,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:  # Unix-like
                subprocess.Popen(
                    ["python", "-m", "qwenpaw"],
                    cwd=qwenpaw_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            pass

    def _cleanup_old_backups(self, backup_dir: str, max_backups: int = 5):
        """Clean up old backups"""
        try:
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
            backup_files.sort(
                key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)),
                reverse=True
            )

            for old_backup in backup_files[max_backups:]:
                old_backup_path = os.path.join(backup_dir, old_backup)
                os.remove(old_backup_path)
        except Exception as e:
            pass


# Register the tool
def get_tool():
    """Get Human Thinking Tool instance"""
    return HumanThinkingTool()
