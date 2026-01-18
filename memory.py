"""记忆模块 - 用于存储和管理对话历史"""
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="角色: system, user, assistant, tool")
    content: Optional[str] = Field(None, description="消息内容")
    tool_call_id: Optional[str] = Field(None, description="工具调用ID（tool消息使用）")
    name: Optional[str] = Field(None, description="工具名称（tool消息使用）")
    tool_calls: Optional[List[dict]] = Field(None, description="工具调用列表（assistant消息使用）")

    def to_dict(self) -> dict:
        """转换为字典格式"""
        msg = {"role": self.role}
        if self.content is not None:
            msg["content"] = self.content
        if self.tool_call_id is not None:
            msg["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            msg["name"] = self.name
        if self.tool_calls is not None:
            msg["tool_calls"] = self.tool_calls
        return msg

    @classmethod
    def user_message(cls, content: str) -> "Message":
        """创建用户消息"""
        return cls(role="user", content=content)

    @classmethod
    def assistant_message(cls, content: Optional[str] = None) -> "Message":
        """创建助手消息"""
        return cls(role="assistant", content=content)

    @classmethod
    def system_message(cls, content: str) -> "Message":
        """创建系统消息"""
        return cls(role="system", content=content)

    @classmethod
    def tool_message(cls, content: str, tool_call_id: str, name: str) -> "Message":
        """创建工具消息"""
        return cls(role="tool", content=content, tool_call_id=tool_call_id, name=name)

    @classmethod
    def from_tool_calls(cls, tool_calls: List[Any], content: Optional[str] = None) -> "Message":
        """从工具调用创建assistant消息"""
        # 将tool_calls转换为字典格式
        formatted_calls = []
        for call in tool_calls:
            if hasattr(call, 'function'):
                # OpenAI格式
                formatted_calls.append({
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments or "{}"
                    }
                })
            elif isinstance(call, dict):
                # 已经是字典格式
                formatted_calls.append(call)

        return cls(role="assistant", content=content, tool_calls=formatted_calls if formatted_calls else None)


class Memory(BaseModel):
    """
    记忆模块 - 管理对话历史

    设计说明：
    1. 存储完整的对话历史（messages列表）
    2. 支持消息的添加、获取、清理
    3. 限制最大消息数量，防止上下文过长
    4. 消息顺序：system -> user -> assistant -> tool -> user -> ...
    """
    messages: List[Message] = Field(default_factory=list, description="消息列表")
    max_messages: int = Field(100, description="最大消息数量")

    def add_message(self, message: Message) -> None:
        """添加消息到记忆"""
        self.messages.append(message)
        # 如果超过最大数量，保留最新的消息
        if len(self.messages) > self.max_messages:
            # 保留第一个system消息（如果有），然后保留最新的消息
            system_msgs = [msg for msg in self.messages if msg.role == "system"]
            other_msgs = [msg for msg in self.messages if msg.role != "system"]

            keep_system = system_msgs[:1]  # 只保留第一个system消息
            keep_others = other_msgs[-(self.max_messages - len(keep_system)):]

            self.messages = keep_system + keep_others

    def add_messages(self, messages: List[Message]) -> None:
        """批量添加消息"""
        for msg in messages:
            self.add_message(msg)

    def clear(self) -> None:
        """清空记忆"""
        self.messages.clear()

    def get_recent_messages(self, n: int) -> List[Message]:
        """获取最近的n条消息"""
        return self.messages[-n:] if n > 0 else self.messages

    def to_dict_list(self) -> List[dict]:
        """转换为字典列表（用于API调用）"""
        return [msg.to_dict() for msg in self.messages]
