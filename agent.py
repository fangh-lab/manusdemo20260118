"""智能体模块 - 简化版"""
import json
from typing import List, Optional

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from memory import Memory, Message
from llm import LLM
from tool.base import BaseTool


class Agent:
    """
    智能体 - 简化版

    核心功能：
    1. 维护对话记忆（Memory）
    2. 通过LLM进行思考和决策
    3. 执行工具调用
    4. 处理工具返回结果
    """

    def __init__(
        self,
        llm: Optional[LLM] = None,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: str = "你是一个有用的AI助手，可以使用工具来帮助用户完成任务。",
    ):
        self.llm = llm or LLM()
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.memory = Memory()

        # 工具映射
        self.tool_map = {tool.name: tool for tool in self.tools}

        # 添加系统消息
        if system_prompt:
            self.memory.add_message(Message.system_message(system_prompt))

    async def run(self, user_input: str, max_steps: int = 10) -> str:
        """
        运行智能体

        Args:
            user_input: 用户输入
            max_steps: 最大执行步骤数

        Returns:
            最终结果
        """
        # 添加用户消息
        self.memory.add_message(Message.user_message(user_input))

        for step in range(max_steps):
            # 思考阶段：LLM决定下一步行动
            response = await self._think()

            if not response:
                break

            # 如果有工具调用，执行工具
            if response.tool_calls:
                await self._act(response.tool_calls)
            else:
                # 没有工具调用，返回内容
                if response.content:
                    self.memory.add_message(Message.assistant_message(response.content))
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
                tool_calls=response.tool_calls,
                content=response.content
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
            tool_calls = list(tool_calls) if hasattr(tool_calls, '__iter__') else []

        for tool_call in tool_calls:
            # 处理不同的tool_call格式
            if hasattr(tool_call, 'function'):
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
                    content=f"错误: 工具'{tool_name}'不存在",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
                self.memory.add_message(tool_msg)
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
                continue

            # 执行工具
            tool = self.tool_map[tool_name]
            try:
                result = await tool.execute(**tool_args)
                result_str = str(result)
            except Exception as e:
                result_str = f"错误: {str(e)}"

            # 添加工具结果消息
            tool_msg = Message.tool_message(
                content=result_str,
                tool_call_id=tool_call_id,
                name=tool_name,
            )
            self.memory.add_message(tool_msg)

    async def cleanup(self):
        """清理资源"""
        for tool in self.tools:
            if hasattr(tool, "cleanup"):
                await tool.cleanup()
