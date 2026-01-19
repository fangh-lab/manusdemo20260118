"""工具基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class ToolResult(BaseModel):
    """工具执行结果"""

    output: Optional[str] = None
    error: Optional[str] = None

    def __str__(self) -> str:
        return self.error if self.error else (self.output or "")


class BaseTool(ABC, BaseModel):
    """工具基类"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def to_param(self) -> Dict:
        """转换为OpenAI函数调用格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
