"""LLM封装模块 - 简化版"""
import asyncio
import json
import time
from typing import List, Optional, Union, Any

from openai import AsyncOpenAI, AsyncAzureOpenAI, APITimeoutError, APIError
from openai.types.chat import ChatCompletionMessage

try:
    from config import config
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import config


class LLM:
    """LLM客户端封装"""

    def __init__(self):
        llm_config = config.llm

        # 根据api_type创建不同的客户端
        if llm_config.api_type == "azure":
            self.client = AsyncAzureOpenAI(
                api_key=llm_config.api_key,
                api_version=llm_config.api_version,
                base_url=llm_config.base_url,
            )
        elif llm_config.api_type == "anthropic":
            # Anthropic使用不同的库，这里简化处理
            # 实际使用时需要安装anthropic库
            try:
                from anthropic import AsyncAnthropic
                self.client = AsyncAnthropic(api_key=llm_config.api_key)
                self._is_anthropic = True
            except ImportError:
                raise ImportError("使用anthropic API需要安装: pip install anthropic")
        else:
            # OpenAI兼容的API（包括ollama等）
            # 修复 base_url：如果是 deepseek，确保有 /v1 路径
            base_url = llm_config.base_url
            if "deepseek.com" in base_url and not base_url.endswith("/v1"):
                if not base_url.endswith("/"):
                    base_url += "/"
                base_url += "v1"

            self.client = AsyncOpenAI(
                api_key=llm_config.api_key,
                base_url=base_url,
                timeout=60.0,  # 设置60秒超时
            )
            self._is_anthropic = False

        self.model = llm_config.model
        self.max_tokens = llm_config.max_tokens
        self.temperature = llm_config.temperature
        self.api_type = llm_config.api_type

    async def ask(
        self,
        messages: List[dict],
        system_msgs: Optional[List[dict]] = None,
    ) -> str:
        """普通对话（不使用工具）"""
        if system_msgs:
            messages = system_msgs + messages

        if self._is_anthropic:
            # Anthropic API处理
            return await self._ask_anthropic(messages)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return response.choices[0].message.content or ""

    async def ask_tool(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        system_msgs: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        max_retries: int = 3,
    ):
        """带工具调用的对话（带重试机制）"""
        if system_msgs:
            messages = system_msgs + messages

        params = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        if self._is_anthropic:
            # Anthropic不支持tools参数，需要转换为messages格式
            # 这里简化处理，实际使用时需要转换
            raise NotImplementedError("Anthropic工具调用需要特殊处理")

        # 重试机制
        last_error = None
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(**params)

                if not response.choices:
                    return None

                return response.choices[0].message

            except (APITimeoutError, APIError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间：2秒、4秒、6秒
                    print(f"⚠️ API调用失败，{wait_time}秒后重试 ({attempt + 1}/{max_retries})...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ API调用失败，已重试{max_retries}次")
                    raise Exception(f"API调用失败: {str(e)}")

        raise Exception(f"API调用失败: {str(last_error)}")

    async def _ask_anthropic(self, messages: List[dict]) -> str:
        """Anthropic API调用"""
        # 将messages转换为anthropic格式
        from anthropic import HUMAN_PROMPT, AI_PROMPT

        # 提取system消息
        system_msg = None
        conversation = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                conversation.append(f"{HUMAN_PROMPT} {msg['content']}")
            elif msg["role"] == "assistant":
                conversation.append(f"{AI_PROMPT} {msg['content']}")

        prompt = "".join(conversation) + AI_PROMPT

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_msg or "",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text if response.content else ""
