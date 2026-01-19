import asyncio
import json
import platform
import socket
import subprocess
import time
from typing import Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from tool.base import BaseTool, ToolResult


class CommandExecuteTool(BaseTool):
    """命令执行工具"""

    name: str = "command_execute"
    description: str = "执行系统命令（安全限制：禁止危险命令）"
    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的命令"},
            "timeout": {
                "type": "integer",
                "description": "超时时间（秒）",
                "default": 30,
                "minimum": 1,
                "maximum": 300,
            },
            "cwd": {"type": "string", "description": "工作目录", "default": "."},
        },
        "required": ["command"],
    }

    async def execute(
        self, command: str, timeout: int = 30, cwd: str = "."
    ) -> ToolResult:
        try:
            # 安全检查：限制危险命令
            dangerous_patterns = [
                "rm -rf",
                "rm -r",
                "format",
                "del /",
                "shutdown",
                "reboot",
                "halt",
                "poweroff",
                "mkfs",
                "dd if=",
                "chmod 777",
                "chown root",
                "> /dev/",
                "| rm",
                "; rm",
                "&& rm",
            ]

            command_lower = command.lower()
            for pattern in dangerous_patterns:
                if pattern in command_lower:
                    return ToolResult(error=f"禁止执行危险命令（包含 '{pattern}'）")

            # 安全检查：限制工作目录
            if ".." in cwd or cwd.startswith("/") or ":" in cwd:
                cwd = "."

            # 执行命令
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                shell=True,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except:
                    pass
                return ToolResult(error=f"命令执行超时（{timeout}秒）")

            output = stdout.decode("utf-8", errors="ignore") if stdout else ""
            error = stderr.decode("utf-8", errors="ignore") if stderr else ""

            # 限制输出长度
            if len(output) > 5000:
                output = output[:5000] + "\n...（输出过长，已截断）"
            if len(error) > 5000:
                error = error[:5000] + "\n...（错误输出过长，已截断）"

            result_info = {
                "return_code": process.returncode,
                "stdout": output,
                "stderr": error,
                "command": command,
            }

            if process.returncode == 0:
                return ToolResult(
                    output=f"命令执行成功：\n{json.dumps(result_info, indent=2, ensure_ascii=False)}"
                )
            else:
                return ToolResult(
                    error=f"命令执行失败：\n{json.dumps(result_info, indent=2, ensure_ascii=False)}"
                )

        except Exception as e:
            return ToolResult(error=f"执行命令失败：{str(e)}")


class SystemInfoTool(BaseTool):
    """系统信息工具"""

    name: str = "system_info"
    description: str = "获取系统信息"
    parameters: dict = {
        "type": "object",
        "properties": {
            "info_type": {
                "type": "string",
                "enum": ["all", "platform", "cpu", "memory", "disk", "network"],
                "description": "信息类型",
                "default": "all",
            }
        },
    }

    async def execute(self, info_type: str = "all") -> ToolResult:
        try:
            info = {}

            if info_type in ["all", "platform"]:
                info["platform"] = {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version(),
                }

            if info_type in ["all", "cpu"]:
                if HAS_PSUTIL:
                    info["cpu"] = {
                        "cores": psutil.cpu_count(),
                        "usage": psutil.cpu_percent(interval=1),
                        "frequency": psutil.cpu_freq().current
                        if hasattr(psutil.cpu_freq(), "current")
                        else None,
                    }
                else:
                    info["cpu"] = {
                        "cores": os.cpu_count() if hasattr(os, "cpu_count") else "未知",
                        "warning": "需要安装psutil库获取详细信息",
                    }

            if info_type in ["all", "memory"]:
                if HAS_PSUTIL:
                    memory = psutil.virtual_memory()
                    info["memory"] = {
                        "total": f"{memory.total / (1024**3):.2f} GB",
                        "available": f"{memory.available / (1024**3):.2f} GB",
                        "used": f"{memory.used / (1024**3):.2f} GB",
                        "percent": f"{memory.percent}%",
                    }
                else:
                    info["memory"] = {"warning": "需要安装psutil库获取内存信息"}

            if info_type in ["all", "disk"]:
                if HAS_PSUTIL:
                    try:
                        disk = psutil.disk_usage(".")
                        info["disk"] = {
                            "total": f"{disk.total / (1024**3):.2f} GB",
                            "used": f"{disk.used / (1024**3):.2f} GB",
                            "free": f"{disk.free / (1024**3):.2f} GB",
                            "percent": f"{disk.percent}%",
                        }
                    except:
                        info["disk"] = {"error": "无法获取磁盘信息"}
                else:
                    info["disk"] = {"warning": "需要安装psutil库获取磁盘信息"}

            if info_type in ["all", "network"]:
                try:
                    info["network"] = {
                        "hostname": socket.gethostname(),
                        "ip_address": socket.gethostbyname(socket.gethostname()),
                    }
                except:
                    info["network"] = {"error": "无法获取网络信息"}

            return ToolResult(output=json.dumps(info, indent=2, ensure_ascii=False))

        except Exception as e:
            return ToolResult(error=f"获取系统信息失败：{str(e)}")


class PythonExecuteTool(BaseTool):
    """Python代码执行工具"""

    name: str = "python_execute"
    description: str = "执行Python代码（安全沙箱环境）"
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的Python代码"},
            "timeout": {
                "type": "integer",
                "description": "超时时间（秒）",
                "default": 10,
                "minimum": 1,
                "maximum": 60,
            },
        },
        "required": ["code"],
    }

    async def execute(self, code: str, timeout: int = 10) -> ToolResult:
        try:
            # 安全检查：禁止危险操作
            dangerous_keywords = [
                "__import__",
                "eval",
                "exec",
                "compile",
                "open(",
                "os.system",
                "subprocess",
                "import os",
                "import sys",
                "import subprocess",
                "import socket",
                "import shutil",
                "import tempfile",
                "import ctypes",
                "import mmap",
            ]

            for keyword in dangerous_keywords:
                if keyword in code:
                    return ToolResult(error=f"代码包含危险操作：'{keyword}'")

            # 创建安全的执行环境
            safe_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "sorted": sorted,
                    "reversed": reversed,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "abs": abs,
                    "round": round,
                    "type": type,
                    "isinstance": isinstance,
                    "issubclass": issubclass,
                }
            }

            # 执行代码
            try:
                # 使用exec在安全环境中执行
                exec_globals = safe_globals.copy()
                exec(code, exec_globals)

                # 尝试获取输出
                output = ""
                if "result" in exec_globals:
                    output = str(exec_globals["result"])
                elif "__result__" in exec_globals:
                    output = str(exec_globals["__result__"])

                return ToolResult(output=f"代码执行成功：\n{output}")

            except Exception as exec_error:
                return ToolResult(error=f"代码执行错误：{str(exec_error)}")

        except Exception as e:
            return ToolResult(error=f"执行Python代码失败：{str(e)}")
