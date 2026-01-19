"""主入口文件 - 增强版（带workspace支持）"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# 确保可以导入模块
sys.path.insert(0, str(Path(__file__).parent))

from agent import Agent
from tool.base import ToolResult

# 导入所有工具
from tool.browser import BrowserTool
from tool.data import JsonTool, MathTool, TextTool
from tool.file import DirectoryListTool, FileReadTool, FileWriteTool
from tool.network import HttpTool, NetworkTestTool, WebSocketTool
from tool.system import CommandExecuteTool, PythonExecuteTool, SystemInfoTool


class WorkspaceManager:
    """工作区管理器"""

    def __init__(self, workspace_path: str = "workspace"):
        self.workspace_path = Path(workspace_path)
        self._ensure_workspace()

    def _ensure_workspace(self):
        """确保工作区目录存在"""
        if not self.workspace_path.exists():
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 创建工作区目录: {self.workspace_path.absolute()}")

        # 创建工作区子目录
        subdirs = ["files", "logs", "data", "outputs", "temp"]
        for subdir in subdirs:
            subdir_path = self.workspace_path / subdir
            if not subdir_path.exists():
                subdir_path.mkdir(exist_ok=True)

    def get_absolute_path(self, relative_path: str) -> Path:
        """获取工作区内的绝对路径"""
        return self.workspace_path / relative_path

    def is_in_workspace(self, path: str) -> bool:
        """检查路径是否在工作区内"""
        try:
            abs_path = Path(path).absolute()
            workspace_abs = self.workspace_path.absolute()
            return str(abs_path).startswith(str(workspace_abs))
        except Exception:
            return False

    def list_workspace(self) -> list:
        """列出工作区内容"""
        result = []
        for item in self.workspace_path.rglob("*"):
            if item.is_file():
                size = item.stat().st_size
                result.append(
                    f"[文件] {item.relative_to(self.workspace_path)} ({size}字节)"
                )
            elif item.is_dir():
                result.append(f"[目录] {item.relative_to(self.workspace_path)}/")
        return result

    def get_workspace_info(self) -> dict:
        """获取工作区信息"""
        total_size = 0
        file_count = 0
        dir_count = 0

        for item in self.workspace_path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1
            elif item.is_dir():
                dir_count += 1

        return {
            "workspace_path": str(self.workspace_path.absolute()),
            "total_size": f"{total_size / 1024:.2f} KB",
            "file_count": file_count,
            "dir_count": dir_count,
            "subdirectories": ["files", "logs", "data", "outputs", "temp"],
        }


class WorkspaceFileTool(FileWriteTool):
    """工作区文件写入工具（继承自FileWriteTool）"""

    workspace_manager: "WorkspaceManager"

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__(
            name="workspace_file_write",
            description="写入内容到工作区文件（自动在工作区内创建文件）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "要写入的内容"},
                    "mode": {
                        "type": "string",
                        "enum": ["w", "a"],
                        "description": "写入模式",
                        "default": "w",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "文件编码",
                        "default": "utf-8",
                    },
                },
                "required": ["path", "content"],
            },
            workspace_manager=workspace_manager,
        )

    async def execute(
        self, path: str, content: str, mode: str = "w", encoding: str = "utf-8"
    ) -> ToolResult:
        """确保文件写入到工作区内"""
        # 如果路径不是绝对路径，或者不在工作区内，则放到workspace/files目录下
        if not self.workspace_manager.is_in_workspace(path):
            # 提取文件名
            filename = Path(path).name
            # 放到workspace/files目录下
            workspace_path = self.workspace_manager.get_absolute_path(
                f"files/{filename}"
            )
            path = str(workspace_path)
            print(f"📝 文件将保存到工作区: {path}")

        return await super().execute(
            path=path, content=content, mode=mode, encoding=encoding
        )


class WorkspaceDirectoryTool(DirectoryListTool):
    """工作区目录列表工具"""

    workspace_manager: "WorkspaceManager"

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__(
            name="workspace_list",
            description="列出工作区目录内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径",
                        "default": ".",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归列出",
                        "default": False,
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "是否显示隐藏文件",
                        "default": False,
                    },
                },
            },
            workspace_manager=workspace_manager,
        )

    async def execute(
        self, path: str = ".", recursive: bool = False, show_hidden: bool = False
    ) -> ToolResult:
        """列出工作区目录"""
        # 如果路径是相对路径，转换为工作区路径
        if not self.workspace_manager.is_in_workspace(path):
            workspace_path = self.workspace_manager.get_absolute_path(path)
            path = str(workspace_path)

        return await super().execute(
            path=path, recursive=recursive, show_hidden=show_hidden
        )


async def main():
    """主函数"""
    print("=" * 60)
    print("FanghaoManus Demo - 增强版多功能智能体（带Workspace）")
    print("=" * 60)
    print("支持工具：浏览器、文件操作、系统命令、数据处理、网络工具")
    print("所有生成的文件将自动保存到 workspace/ 目录")
    print("输入 'exit'、'quit' 或 '退出' 结束程序")
    print("-" * 60)

    # 初始化工作区管理器
    workspace = WorkspaceManager("workspace")
    workspace_info = workspace.get_workspace_info()
    print(f"📁 工作区路径: {workspace_info['workspace_path']}")
    print(
        f"📊 工作区状态: {workspace_info['file_count']}个文件, {workspace_info['total_size']}"
    )
    print(f"📂 子目录: {', '.join(workspace_info['subdirectories'])}")
    print("-" * 60)

    # 创建所有工具实例
    tools = []

    # 1. 浏览器工具
    browser_tool = BrowserTool()
    tools.append(browser_tool)
    print("✅ 浏览器工具已加载")

    # 2. 文件操作工具（使用工作区版本）
    file_read_tool = FileReadTool()
    file_write_tool = WorkspaceFileTool(workspace)  # 使用工作区版本
    directory_list_tool = WorkspaceDirectoryTool(workspace)  # 使用工作区版本
    tools.extend([file_read_tool, file_write_tool, directory_list_tool])
    print("✅ 文件操作工具已加载（读取、工作区写入、工作区目录列表）")

    # 3. 系统操作工具
    command_tool = CommandExecuteTool()
    system_info_tool = SystemInfoTool()
    python_execute_tool = PythonExecuteTool()
    tools.extend([command_tool, system_info_tool, python_execute_tool])
    print("✅ 系统操作工具已加载（命令执行、系统信息、Python执行）")

    # 4. 数据处理工具
    json_tool = JsonTool()
    text_tool = TextTool()
    math_tool = MathTool()
    tools.extend([json_tool, text_tool, math_tool])
    print("✅ 数据处理工具已加载（JSON处理、文本处理、数学计算）")

    # 5. 网络工具
    http_tool = HttpTool()
    network_test_tool = NetworkTestTool()
    websocket_tool = WebSocketTool()
    tools.extend([http_tool, network_test_tool, websocket_tool])
    print("✅ 网络工具已加载（HTTP请求、网络测试、WebSocket）")

    print(f"📊 总计加载 {len(tools)} 个工具")
    print("-" * 60)

    # 创建智能体（传入所有工具）
    agent = Agent(
        tools=tools,
        system_prompt=f"""你是一个多功能AI助手，可以使用以下工具帮助用户：

## 可用工具分类：

### 1. 浏览器工具 (browser)
- 浏览网页、点击元素、输入文本、滚动页面
- 获取页面状态、等待、返回上一页

### 2. 文件操作工具（自动保存到工作区）
- file_read: 读取文件内容
- workspace_file_write: 写入内容到文件（自动保存到workspace/files目录）
- workspace_list: 列出工作区目录内容

### 3. 系统操作工具
- command_execute: 执行系统命令（安全限制）
- system_info: 获取系统信息（CPU、内存、磁盘等）
- python_execute: 执行Python代码（安全沙箱）

### 4. 数据处理工具
- json_process: JSON处理（解析、验证、查询、格式化）
- text_process: 文本处理（统计、搜索、替换、分割）
- math_calculate: 数学计算（基本运算、统计、单位转换）

### 5. 网络工具
- http_request: 发送HTTP请求（GET、POST等）
- network_test: 网络测试（Ping、TCP连接、HTTP测试）
- websocket: WebSocket连接和消息发送

## 工作区说明：
所有生成的文件将自动保存到工作区目录：{workspace_info["workspace_path"]}
工作区包含以下子目录：
- files/: 用户生成的文件
- logs/: 日志文件
- data/: 数据文件
- outputs/: 输出文件
- temp/: 临时文件

## 使用指南：
1. 根据用户需求选择合适的工具
2. 文件操作会自动保存到工作区，无需指定完整路径
3. 仔细阅读工具描述和参数要求
4. 提供完整的参数信息
5. 处理工具返回的结果
6. 如果操作失败，根据错误信息调整策略

## 安全注意事项：
- 文件操作：自动限制到工作区内，避免访问系统文件
- 命令执行：禁止危险命令，限制执行时间
- 网络访问：限制访问本地网络地址
- 代码执行：在安全沙箱中执行Python代码

请根据用户的具体需求，选择最合适的工具来完成任务。""",
    )

    try:
        # 交互式循环
        while True:
            user_input = input("\n👤 你: ").strip()

            if user_input.lower() in ["exit", "quit", "退出"]:
                print("\n👋 再见！")
                break

            if not user_input:
                continue

            print("\n🤔 思考中...")
            try:
                result = await agent.run(user_input, max_steps=15)
                print(f"\n🤖 助手: {result}")
            except Exception as e:
                print(f"\n❌ 错误: {str(e)}")
                print("💡 提示：请检查网络连接或API配置")

    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被中断")
    finally:
        # 清理资源
        print("\n🧹 清理资源中...")
        try:
            await agent.cleanup()
            print("✅ 资源清理完成")

            # 显示最终工作区状态
            final_info = workspace.get_workspace_info()
            print(
                f"📁 最终工作区状态: {final_info['file_count']}个文件, {final_info['total_size']}"
            )

        except Exception as e:
            print(f"⚠️ 资源清理时出错: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
