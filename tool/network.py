import asyncio
import json
import socket
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import aiohttp

from tool.base import BaseTool, ToolResult


class HttpTool(BaseTool):
    """HTTP请求工具"""

    name: str = "http_request"
    description: str = "发送HTTP请求（GET、POST、PUT、DELETE等）"
    parameters: dict = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                "description": "HTTP方法",
                "default": "GET",
            },
            "url": {"type": "string", "description": "请求URL"},
            "headers": {
                "type": "string",
                "description": "请求头（JSON格式）",
                "default": "{}",
            },
            "body": {"type": "string", "description": "请求体（JSON或文本）"},
            "params": {
                "type": "string",
                "description": "URL查询参数（JSON格式）",
                "default": "{}",
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间（秒）",
                "default": 30,
                "minimum": 1,
                "maximum": 300,
            },
            "verify_ssl": {
                "type": "boolean",
                "description": "是否验证SSL证书",
                "default": True,
            },
        },
        "required": ["url"],
    }

    async def execute(
        self,
        method: str = "GET",
        url: str = None,
        headers: str = "{}",
        body: Optional[str] = None,
        params: str = "{}",
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> ToolResult:
        try:
            # 安全检查：验证URL格式
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ToolResult(error=f"无效的URL格式：{url}")

            # 安全检查：限制访问本地网络
            if parsed_url.hostname in ["localhost", "127.0.0.1", "::1", "0.0.0.0"]:
                return ToolResult(error="禁止访问本地网络地址")

            # 解析headers和params
            try:
                headers_dict = json.loads(headers)
                params_dict = json.loads(params)
            except json.JSONDecodeError as e:
                return ToolResult(error=f"JSON解析失败：{str(e)}")

            # 准备请求数据
            request_data = None
            content_type = headers_dict.get("Content-Type", "")

            if body:
                if "application/json" in content_type:
                    try:
                        request_data = json.dumps(json.loads(body))
                    except json.JSONDecodeError:
                        request_data = body
                else:
                    request_data = body

            # 发送HTTP请求
            start_time = time.time()
            try:
                connector = aiohttp.TCPConnector(ssl=verify_ssl)
                timeout_obj = aiohttp.ClientTimeout(total=timeout)

                async with aiohttp.ClientSession(
                    connector=connector, timeout=timeout_obj
                ) as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers_dict,
                        params=params_dict,
                        data=request_data,
                    ) as response:
                        response_time = time.time() - start_time

                        # 读取响应内容
                        response_text = await response.text()

                        # 限制响应长度
                        if len(response_text) > 10000:
                            response_text = (
                                response_text[:10000] + "\n...（响应过长，已截断）"
                            )

                        # 构建结果
                        result = {
                            "status": response.status,
                            "status_text": response.reason,
                            "headers": dict(response.headers),
                            "response_time": f"{response_time:.2f}秒",
                            "url": str(response.url),
                            "body": response_text,
                        }

                        if response.status >= 400:
                            return ToolResult(
                                error=f"HTTP请求失败：\n{json.dumps(result, indent=2, ensure_ascii=False)}"
                            )
                        else:
                            return ToolResult(
                                output=f"HTTP请求成功：\n{json.dumps(result, indent=2, ensure_ascii=False)}"
                            )

            except asyncio.TimeoutError:
                return ToolResult(error=f"HTTP请求超时（{timeout}秒）")
            except aiohttp.ClientError as e:
                return ToolResult(error=f"HTTP客户端错误：{str(e)}")

        except Exception as e:
            return ToolResult(error=f"HTTP请求失败：{str(e)}")


class NetworkTestTool(BaseTool):
    """网络测试工具"""

    name: str = "network_test"
    description: str = "网络连通性测试（Ping、TCP连接、HTTP测试）"
    parameters: dict = {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "测试目标（IP地址或域名）"},
            "port": {
                "type": "integer",
                "description": "端口号（TCP测试使用）",
                "default": 80,
                "minimum": 1,
                "maximum": 65535,
            },
            "test_type": {
                "type": "string",
                "enum": ["ping", "tcp", "http", "dns"],
                "description": "测试类型",
                "default": "ping",
            },
            "count": {
                "type": "integer",
                "description": "测试次数（Ping测试使用）",
                "default": 4,
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["target"],
    }

    async def execute(
        self,
        target: str,
        port: int = 80,
        test_type: str = "ping",
        count: int = 4,
    ) -> ToolResult:
        try:
            # 安全检查：限制访问本地网络
            if target in ["localhost", "127.0.0.1", "::1", "0.0.0.0"]:
                return ToolResult(error="禁止测试本地网络地址")

            if test_type == "ping":
                # Ping测试（使用系统ping命令）
                try:
                    import platform
                    import subprocess

                    # 根据操作系统选择ping命令
                    if platform.system().lower() == "windows":
                        ping_cmd = ["ping", "-n", str(count), target]
                    else:
                        ping_cmd = ["ping", "-c", str(count), target]

                    process = await asyncio.create_subprocess_exec(
                        *ping_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                    stdout, stderr = await process.communicate()
                    output = stdout.decode("utf-8", errors="ignore")

                    if process.returncode == 0:
                        return ToolResult(output=f"Ping测试成功：\n{output}")
                    else:
                        return ToolResult(error=f"Ping测试失败：\n{output}")

                except (FileNotFoundError, subprocess.SubprocessError) as e:
                    return ToolResult(error=f"Ping测试执行失败：{str(e)}")

            elif test_type == "tcp":
                # TCP连接测试
                start_time = time.time()
                try:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(target, port), timeout=10
                    )
                    writer.close()
                    await writer.wait_closed()

                    latency = (time.time() - start_time) * 1000
                    return ToolResult(
                        output=f"TCP连接成功：{target}:{port}\n延迟：{latency:.2f}ms"
                    )

                except (ConnectionRefusedError, ConnectionResetError) as e:
                    return ToolResult(error=f"TCP连接被拒绝：{str(e)}")
                except asyncio.TimeoutError:
                    return ToolResult(error="TCP连接超时（10秒）")
                except OSError as e:
                    return ToolResult(error=f"TCP连接失败：{str(e)}")

            elif test_type == "http":
                # HTTP测试（使用HttpTool）
                http_tool = HttpTool()
                result = await http_tool.execute(
                    method="GET",
                    url=f"http://{target}:{port}" if port != 80 else f"http://{target}",
                    timeout=10,
                )

                if result.error:
                    return ToolResult(error=f"HTTP测试失败：{result.error}")
                else:
                    return ToolResult(output=f"HTTP测试成功：\n{result.output}")

            elif test_type == "dns":
                # DNS解析测试
                start_time = time.time()
                try:
                    # 使用socket进行DNS解析
                    ip_address = await asyncio.get_event_loop().getaddrinfo(
                        target, None
                    )
                    resolve_time = (time.time() - start_time) * 1000

                    ips = []
                    for result in ip_address[:5]:  # 限制显示前5个IP
                        ips.append(result[4][0])

                    return ToolResult(
                        output=f"DNS解析成功：{target}\nIP地址：{', '.join(ips)}\n解析时间：{resolve_time:.2f}ms"
                    )

                except socket.gaierror as e:
                    return ToolResult(error=f"DNS解析失败：{str(e)}")

            else:
                return ToolResult(error=f"不支持的测试类型：{test_type}")

        except Exception as e:
            return ToolResult(error=f"网络测试失败：{str(e)}")


class WebSocketTool(BaseTool):
    """WebSocket工具"""

    name: str = "websocket"
    description: str = "WebSocket连接和消息发送"
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "WebSocket URL（ws://或wss://）"},
            "action": {
                "type": "string",
                "enum": ["connect", "send", "close"],
                "description": "操作类型",
                "default": "connect",
            },
            "message": {
                "type": "string",
                "description": "要发送的消息（send操作需要）",
            },
            "timeout": {
                "type": "integer",
                "description": "超时时间（秒）",
                "default": 30,
                "minimum": 1,
                "maximum": 300,
            },
        },
        "required": ["url", "action"],
    }

    # 添加websocket字段声明
    websocket: Optional[Any] = None

    def __init__(self):
        super().__init__()

    async def execute(
        self,
        url: str,
        action: str = "connect",
        message: Optional[str] = None,
        timeout: int = 30,
    ) -> ToolResult:
        try:
            # 安全检查：验证URL格式
            if not url.startswith(("ws://", "wss://")):
                return ToolResult(error="WebSocket URL必须以ws://或wss://开头")

            if action == "connect":
                # 连接WebSocket
                if self.websocket:
                    return ToolResult(error="WebSocket已连接，请先关闭")

                try:
                    self.websocket = await aiohttp.ClientSession().ws_connect(
                        url, timeout=timeout
                    )
                    return ToolResult(output=f"WebSocket连接成功：{url}")

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    return ToolResult(error=f"WebSocket连接失败：{str(e)}")

            elif action == "send":
                # 发送消息
                if not self.websocket:
                    return ToolResult(error="WebSocket未连接，请先连接")

                if not message:
                    return ToolResult(error="send操作需要message参数")

                try:
                    await self.websocket.send_str(message)

                    # 等待响应（可选）
                    response = await asyncio.wait_for(
                        self.websocket.receive(), timeout=timeout
                    )

                    if response.type == aiohttp.WSMsgType.TEXT:
                        return ToolResult(
                            output=f"消息发送成功，收到响应：\n{response.data}"
                        )
                    elif response.type == aiohttp.WSMsgType.CLOSE:
                        return ToolResult(output="消息发送成功，连接已关闭")
                    else:
                        return ToolResult(output="消息发送成功")

                except asyncio.TimeoutError:
                    return ToolResult(error="等待响应超时")
                except aiohttp.ClientError as e:
                    return ToolResult(error=f"消息发送失败：{str(e)}")

            elif action == "close":
                # 关闭连接
                if not self.websocket:
                    return ToolResult(error="WebSocket未连接")

                try:
                    await self.websocket.close()
                    self.websocket = None
                    return ToolResult(output="WebSocket连接已关闭")

                except aiohttp.ClientError as e:
                    return ToolResult(error=f"关闭连接失败：{str(e)}")

            else:
                return ToolResult(error=f"不支持的WebSocket操作：{action}")

        except Exception as e:
            return ToolResult(error=f"WebSocket操作失败：{str(e)}")

    async def cleanup(self):
        """清理WebSocket连接"""
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None
