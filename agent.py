"""智能体模块 - 增强版"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from llm import LLM
from memory import Memory, Message
from tool.base import BaseTool


class Agent:
    """
    智能体 - 增强版

    核心功能：
    1. 维护对话记忆（Memory）
    2. 通过LLM进行思考和决策
    3. 执行工具调用
    4. 处理工具返回结果
    5. 工具使用统计和权限控制
    """

    def __init__(
        self,
        llm: Optional[LLM] = None,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: str = "你是一个有用的AI助手，可以使用工具来帮助用户完成任务。",
        allowed_tools: Optional[List[str]] = None,
        max_tool_usage: int = 100,
        enable_statistics: bool = True,
    ):
        self.llm = llm or LLM()
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.memory = Memory()

        # 权限控制：只允许特定的工具
        if allowed_tools:
            self.tools = [t for t in self.tools if t.name in allowed_tools]
            print(f"🔒 权限控制：启用 {len(self.tools)}/{len(tools or [])} 个工具")

        # 工具映射
        self.tool_map = {tool.name: tool for tool in self.tools}

        # 工具使用统计
        self.enable_statistics = enable_statistics
        self.tool_usage_stats: Dict[str, Dict[str, Any]] = {}
        self.total_tool_calls = 0
        self.max_tool_usage = max_tool_usage

        # 初始化统计信息
        for tool in self.tools:
            self.tool_usage_stats[tool.name] = {
                "count": 0,
                "success": 0,
                "error": 0,
                "total_time": 0.0,
                "last_used": None,
            }

        # 添加系统消息
        if system_prompt:
            self.memory.add_message(Message.system_message(system_prompt))

        print(f"🤖 智能体初始化完成，加载 {len(self.tools)} 个工具")

    async def run(self, user_input: str, max_steps: int = 15) -> str:
        """
        运行智能体

        Args:
            user_input: 用户输入
            max_steps: 最大执行步骤数

        Returns:
            最终结果
        """
        print(f"📝 用户输入：{user_input[:50]}{'...' if len(user_input) > 50 else ''}")

        # 添加用户消息
        self.memory.add_message(Message.user_message(user_input))

        for step in range(max_steps):
            if self.total_tool_calls >= self.max_tool_usage:
                print(f"⚠️ 工具使用次数达到上限（{self.max_tool_usage}次）")
                return "工具使用次数达到上限，请重新启动程序"

            print(f"🔄 步骤 {step + 1}/{max_steps}")

            # 思考阶段：LLM决定下一步行动
            response = await self._think()

            if not response:
                print("❌ LLM未返回响应")
                break

            # 如果有工具调用，执行工具
            if response.tool_calls:
                await self._act(response.tool_calls)
            else:
                # 没有工具调用，返回内容
                if response.content:
                    self.memory.add_message(Message.assistant_message(response.content))
                    print(f"✅ 任务完成，共使用 {self.total_tool_calls} 次工具")
                    break

        # 返回最后的助手消息
        if self.memory.messages:
            last_msg = self.memory.messages[-1]
            if last_msg.role == "assistant":
                return last_msg.content or ""

        return "执行完成"

    async def _think(self):
        """思考阶段：调用LLM获取响应"""
        # 准备工具参数
        tools = [tool.to_param() for tool in self.tools]

        if self.enable_statistics and self.total_tool_calls > 0:
            # 可选：将工具使用统计信息添加到系统提示中
            stats_summary = self._get_tool_stats_summary()
            print(f"📊 工具使用统计：{stats_summary}")

        # 调用LLM
        response = await self.llm.ask_tool(
            messages=self.memory.to_dict_list(),
            tools=tools if tools else None,
            tool_choice="auto",
        )

        if not response:
            return None

        # 添加助手消息到记忆（如果有tool_calls，需要包含在消息中）
        if response.tool_calls:
            # 使用from_tool_calls创建包含tool_calls的assistant消息
            assistant_msg = Message.from_tool_calls(
                tool_calls=response.tool_calls, content=response.content
            )
        else:
            # 普通assistant消息
            assistant_msg = Message.assistant_message(response.content)

        self.memory.add_message(assistant_msg)

        return response

    async def _act(self, tool_calls):
        """行动阶段：执行工具调用"""
        # tool_calls可能是列表或对象属性
        if not isinstance(tool_calls, list):
            tool_calls = list(tool_calls) if hasattr(tool_calls, "__iter__") else []

        for tool_call in tool_calls:
            # 处理不同的tool_call格式
            if hasattr(tool_call, "function"):
                # OpenAI格式: tool_call.function.name
                tool_name = tool_call.function.name
                tool_args_str = tool_call.function.arguments or "{}"
                tool_call_id = tool_call.id
            elif isinstance(tool_call, dict):
                # 字典格式
                tool_name = tool_call.get("function", {}).get("name")
                tool_args_str = tool_call.get("function", {}).get("arguments", "{}")
                tool_call_id = tool_call.get("id", "")
            else:
                continue

            if not tool_name:
                continue

            if tool_name not in self.tool_map:
                # 工具不存在
                tool_msg = Message.tool_message(
                    content=f"错误: 工具'{tool_name}'不存在或未授权",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
                self.memory.add_message(tool_msg)
                print(f"❌ 工具 '{tool_name}' 不存在或未授权")
                continue

            # 解析参数
            try:
                tool_args = json.loads(tool_args_str) if tool_args_str else {}
            except json.JSONDecodeError:
                tool_msg = Message.tool_message(
                    content=f"错误: 工具参数格式无效: {tool_args_str}",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
                self.memory.add_message(tool_msg)
                print(f"❌ 工具 '{tool_name}' 参数格式无效")
                continue

            # 执行工具（带统计）
            tool = self.tool_map[tool_name]
            start_time = time.time()

            try:
                print(f"🛠️  执行工具：{tool_name}，参数：{tool_args}")
                result = await tool.execute(**tool_args)
                execution_time = time.time() - start_time
                result_str = str(result)

                # 更新统计信息
                self._update_tool_stats(tool_name, True, execution_time)
                self.total_tool_calls += 1

                if result.error:
                    print(f"⚠️  工具 '{tool_name}' 执行失败：{result.error[:100]}")
                else:
                    print(
                        f"✅  工具 '{tool_name}' 执行成功，耗时：{execution_time:.2f}秒"
                    )

            except Exception as e:
                execution_time = time.time() - start_time
                result_str = f"错误: {str(e)}"

                # 更新统计信息
                self._update_tool_stats(tool_name, False, execution_time)
                self.total_tool_calls += 1

                print(f"❌ 工具 '{tool_name}' 执行异常：{str(e)[:100]}")

            # 添加工具结果消息
            tool_msg = Message.tool_message(
                content=result_str,
                tool_call_id=tool_call_id,
                name=tool_name,
            )
            self.memory.add_message(tool_msg)

    def _update_tool_stats(self, tool_name: str, success: bool, execution_time: float):
        """更新工具使用统计"""
        if not self.enable_statistics or tool_name not in self.tool_usage_stats:
            return

        stats = self.tool_usage_stats[tool_name]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["last_used"] = time.time()

        if success:
            stats["success"] += 1
        else:
            stats["error"] += 1

    def _get_tool_stats_summary(self) -> str:
        """获取工具使用统计摘要"""
        if not self.enable_statistics or not self.tool_usage_stats:
            return "无统计信息"

        summary = []
        for tool_name, stats in self.tool_usage_stats.items():
            if stats["count"] > 0:
                success_rate = (stats["success"] / stats["count"]) * 100
                avg_time = (
                    stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
                )
                summary.append(
                    f"{tool_name}: {stats['count']}次 "
                    f"({success_rate:.1f}%成功) "
                    f"平均{avg_time:.2f}秒"
                )

        return "; ".join(summary) if summary else "无使用记录"

    def get_detailed_stats(self) -> Dict[str, Any]:
        """获取详细统计信息"""
        return {
            "total_tool_calls": self.total_tool_calls,
            "max_tool_usage": self.max_tool_usage,
            "remaining_calls": self.max_tool_usage - self.total_tool_calls,
            "tool_usage": self.tool_usage_stats,
            "memory_size": len(self.memory.messages),
        }

    def reset_statistics(self):
        """重置统计信息"""
        self.total_tool_calls = 0
        for tool_name in self.tool_usage_stats:
            self.tool_usage_stats[tool_name] = {
                "count": 0,
                "success": 0,
                "error": 0,
                "total_time": 0.0,
                "last_used": None,
            }
        print("📊 统计信息已重置")

    async def cleanup(self):
        """清理资源"""
        print("🧹 开始清理资源...")
        cleanup_count = 0

        for tool in self.tools:
            if hasattr(tool, "cleanup"):
                try:
                    await tool.cleanup()
                    cleanup_count += 1
                except Exception as e:
                    print(f"⚠️  清理工具 '{tool.name}' 时出错：{str(e)}")

        # 打印最终统计信息
        if self.enable_statistics:
            print(f"📊 最终统计：共使用 {self.total_tool_calls} 次工具")
            print(f"📊 工具统计摘要：{self._get_tool_stats_summary()}")

        print(f"✅ 资源清理完成，清理了 {cleanup_count} 个工具")

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取可用工具列表"""
        tools_info = []
        for tool in self.tools:
            tools_info.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "usage_count": self.tool_usage_stats.get(tool.name, {}).get(
                        "count", 0
                    ),
                }
            )
        return tools_info
