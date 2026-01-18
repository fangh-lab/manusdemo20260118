"""配置文件加载模块"""
import tomllib
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM配置"""
    model: str = Field(..., description="模型名称")
    base_url: str = Field(..., description="API基础URL")
    api_key: str = Field(..., description="API密钥")
    max_tokens: int = Field(4096, description="最大token数")
    temperature: float = Field(1.0, description="温度参数")
    api_type: str = Field("openai", description="API类型: openai, azure, ollama, anthropic")
    api_version: Optional[str] = Field(None, description="Azure API版本（仅Azure需要）")


class BrowserConfig(BaseModel):
    """浏览器配置"""
    headless: bool = Field(False, description="是否无头模式")
    disable_security: bool = Field(True, description="是否禁用安全特性")


class Config(BaseModel):
    """全局配置"""
    llm: LLMConfig
    browser: Optional[BrowserConfig] = Field(None, description="浏览器配置")


def load_config(config_path: Optional[Path] = None) -> Config:
    """加载配置文件"""
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "config.toml"

    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "rb") as f:
        config_data = tomllib.load(f)

    return Config(**config_data)


# 全局配置实例
config = load_config()
