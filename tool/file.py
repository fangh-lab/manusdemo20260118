from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from tool.base import BaseTool, ToolResult


class FileReadTool(BaseTool):
    """文件读取工具"""

    name: str = "file_read"
    description: str = "读取文件内容"
    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "encoding": {
                "type": "string",
                "description": "文件编码",
                "default": "utf-8",
            },
        },
        "required": ["path"],
    }

    async def execute(self, path: str, encoding: str = "utf-8") -> ToolResult:
        try:
            # 安全检查：限制路径范围
            if not os.path.exists(path):
                return ToolResult(error=f"文件不存在：{path}")

            # 安全检查：避免读取过大文件
            file_size = os.path.getsize(path)
            if file_size > 10 * 1024 * 1024:  # 10MB限制
                return ToolResult(error=f"文件过大（{file_size}字节），超过10MB限制")

            # 读取文件
            with open(path, "r", encoding=encoding) as f:
                content = f.read()

            # 限制输出长度
            if len(content) > 10000:
                content = content[:10000] + "\n...（内容过长，已截断）"

            return ToolResult(output=f"文件内容：\n{content}")
        except UnicodeDecodeError:
            return ToolResult(error=f"文件编码错误，请尝试其他编码")
        except Exception as e:
            return ToolResult(error=f"读取文件失败：{str(e)}")


class FileWriteTool(BaseTool):
    """文件写入工具"""

    name: str = "file_write"
    description: str = "写入内容到文件"
    parameters: dict = {
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
    }

    async def execute(
        self, path: str, content: str, mode: str = "w", encoding: str = "utf-8"
    ) -> ToolResult:
        try:
            # 安全检查：确保目录存在
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # 安全检查：避免写入过大内容
            if len(content) > 5 * 1024 * 1024:  # 5MB限制
                return ToolResult(error="写入内容过大，超过5MB限制")

            # 写入文件
            with open(path, mode, encoding=encoding) as f:
                f.write(content)

            return ToolResult(output=f"成功写入文件：{path}")
        except Exception as e:
            return ToolResult(error=f"写入文件失败：{str(e)}")


class DirectoryListTool(BaseTool):
    """目录列表工具"""

    name: str = "directory_list"
    description: str = "列出目录内容"
    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "目录路径", "default": "."},
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
    }

    async def execute(
        self, path: str = ".", recursive: bool = False, show_hidden: bool = False
    ) -> ToolResult:
        try:
            # 安全检查：确保路径存在
            if not os.path.exists(path):
                return ToolResult(error=f"目录不存在：{path}")

            # 安全检查：确保是目录
            if not os.path.isdir(path):
                return ToolResult(error=f"路径不是目录：{path}")

            result = []

            if recursive:
                for root, dirs, files in os.walk(path):
                    # 过滤隐藏文件
                    if not show_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith(".")]
                        files = [f for f in files if not f.startswith(".")]

                    for name in sorted(dirs):
                        full_path = os.path.join(root, name)
                        result.append(f"[目录] {full_path}/")

                    for name in sorted(files):
                        full_path = os.path.join(root, name)
                        file_size = os.path.getsize(full_path)
                        result.append(f"[文件] {full_path} ({file_size}字节)")
            else:
                items = os.listdir(path)
                if not show_hidden:
                    items = [item for item in items if not item.startswith(".")]

                for name in sorted(items):
                    full_path = os.path.join(path, name)
                    if os.path.isdir(full_path):
                        result.append(f"[目录] {name}/")
                    else:
                        file_size = os.path.getsize(full_path)
                        result.append(f"[文件] {name} ({file_size}字节)")

            if not result:
                return ToolResult(output="目录为空")

            return ToolResult(output="\n".join(result))
        except Exception as e:
            return ToolResult(error=f"列出目录失败：{str(e)}")
