"""浏览器工具 - 简化版"""
import asyncio
import base64
import json
from typing import Optional

from browser_use import Browser as BrowserUseBrowser
from browser_use import BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import Field

from config import config
from tool.base import BaseTool, ToolResult


_BROWSER_DESCRIPTION = """\
浏览器自动化工具，可以控制浏览器进行各种操作。
* 这个工具维护浏览器会话状态，在显式关闭之前保持浏览器会话存活
* 用于浏览网页、填写表单、点击按钮、提取内容等操作
"""


class BrowserTool(BaseTool):
    """浏览器工具"""

    name: str = "browser"
    description: str = _BROWSER_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "go_to_url",
                    "click_element",
                    "input_text",
                    "scroll_down",
                    "scroll_up",
                    "go_back",
                    "get_state",
                    "wait",
                ],
                "description": "要执行的浏览器操作",
            },
            "url": {
                "type": "string",
                "description": "URL（用于go_to_url操作）",
            },
            "index": {
                "type": "integer",
                "description": "元素索引（用于click_element、input_text操作）",
            },
            "text": {
                "type": "string",
                "description": "文本（用于input_text操作）",
            },
            "scroll_amount": {
                "type": "integer",
                "description": "滚动像素数（用于scroll_down、scroll_up操作）",
            },
            "seconds": {
                "type": "integer",
                "description": "等待秒数（用于wait操作）",
            },
        },
        "required": ["action"],
    }

    browser: Optional[BrowserUseBrowser] = Field(default=None, exclude=True)
    context: Optional[BrowserContext] = Field(default=None, exclude=True)
    lock: asyncio.Lock = Field(default_factory=asyncio.Lock, exclude=True)

    async def _ensure_browser_initialized(self) -> BrowserContext:
        """确保浏览器已初始化"""
        if self.browser is None:
            browser_config_kwargs = {
                "headless": config.browser.headless if config.browser else False,
                "disable_security": config.browser.disable_security if config.browser else True,
            }
            self.browser = BrowserUseBrowser(BrowserConfig(**browser_config_kwargs))

        if self.context is None:
            context_config = BrowserContextConfig()
            self.context = await self.browser.new_context(context_config)

        return self.context

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        seconds: Optional[int] = None,
        **kwargs,
    ) -> ToolResult:
        """执行浏览器操作"""
        async with self.lock:
            try:
                context = await self._ensure_browser_initialized()

                # 导航操作
                if action == "go_to_url":
                    if not url:
                        return ToolResult(error="go_to_url操作需要url参数")
                    try:
                        page = await context.get_current_page()
                        await page.goto(url, wait_until="networkidle", timeout=30000)
                        await page.wait_for_load_state("networkidle", timeout=10000)
                        return ToolResult(output=f"已导航到: {url}。页面已加载完成，可以使用get_state查看页面元素。")
                    except Exception as e:
                        error_msg = str(e)
                        if "Timeout" in error_msg:
                            return ToolResult(
                                error=f"页面加载超时: {url}。可能是网络问题或页面加载过慢。"
                            )
                        return ToolResult(error=f"导航失败: {error_msg}")

                elif action == "go_back":
                    await context.go_back()
                    return ToolResult(output="已返回上一页")

                # 元素交互操作
                elif action == "click_element":
                    if index is None:
                        return ToolResult(error="click_element操作需要index参数")
                    try:
                        # 先等待页面稳定
                        page = await context.get_current_page()
                        await page.wait_for_load_state("networkidle", timeout=5000)

                        element = await context.get_dom_element_by_index(index)
                        if not element:
                            # 建议先获取页面状态查看可用元素
                            return ToolResult(
                                error=f"未找到索引为{index}的元素。建议先使用get_state操作查看当前页面的可用元素列表。"
                            )

                        # 尝试点击元素（browser-use内部会处理滚动和可见性问题）
                        try:
                            await context._click_element_node(element)
                            return ToolResult(output=f"已点击索引为{index}的元素")
                        except Exception as click_error:
                            error_msg = str(click_error)
                            # 如果是滚动超时但元素存在，尝试先滚动再点击
                            if "scroll_into_view" in error_msg or "not visible" in error_msg.lower():
                                # 尝试先滚动到元素位置
                                try:
                                    await context.execute_javascript(
                                        f"""
                                        const elements = document.querySelectorAll('*');
                                        const targetIndex = {index};
                                        if (elements[targetIndex]) {{
                                            elements[targetIndex].scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                        }}
                                        """
                                    )
                                    await asyncio.sleep(0.5)  # 等待滚动完成
                                    # 再次尝试点击
                                    await context._click_element_node(element)
                                    return ToolResult(output=f"已点击索引为{index}的元素（已自动滚动到元素位置）")
                                except Exception as retry_error:
                                    return ToolResult(
                                        error=f"点击元素失败：元素可能不可见或无法交互。错误: {str(retry_error)}。建议先使用get_state查看页面状态，或使用scroll_down滚动页面。"
                                    )
                            raise click_error
                    except Exception as e:
                        error_msg = str(e)
                        if "Timeout" in error_msg or "timeout" in error_msg:
                            return ToolResult(
                                error=f"操作超时：元素可能不可见或页面未完全加载。建议先使用get_state查看页面状态，或使用wait操作等待页面加载完成。"
                            )
                        elif "closed" in error_msg.lower():
                            return ToolResult(
                                error=f"浏览器已关闭。请重新打开页面。"
                            )
                        return ToolResult(error=f"点击元素失败: {error_msg}")

                elif action == "input_text":
                    if index is None or not text:
                        return ToolResult(error="input_text操作需要index和text参数")
                    try:
                        # 先等待页面稳定
                        page = await context.get_current_page()
                        await page.wait_for_load_state("networkidle", timeout=5000)

                        element = await context.get_dom_element_by_index(index)
                        if not element:
                            return ToolResult(
                                error=f"未找到索引为{index}的元素。建议先使用get_state操作查看当前页面的可用元素列表。"
                            )

                        # 尝试输入文本（browser-use内部会处理滚动和可见性问题）
                        try:
                            await context._input_text_element_node(element, text)
                            return ToolResult(output=f"已在索引{index}的元素中输入: {text}")
                        except Exception as input_error:
                            error_msg = str(input_error)
                            # 如果是滚动超时但元素存在，尝试先滚动再输入
                            if "scroll_into_view" in error_msg or "not visible" in error_msg.lower():
                                try:
                                    # 尝试先滚动到元素位置
                                    await context.execute_javascript(
                                        f"""
                                        const elements = document.querySelectorAll('*');
                                        const targetIndex = {index};
                                        if (elements[targetIndex]) {{
                                            elements[targetIndex].scrollIntoView({{behavior: 'smooth', block: 'center'}});
                                        }}
                                        """
                                    )
                                    await asyncio.sleep(0.5)  # 等待滚动完成
                                    # 再次尝试输入
                                    await context._input_text_element_node(element, text)
                                    return ToolResult(output=f"已在索引{index}的元素中输入: {text}（已自动滚动到元素位置）")
                                except Exception as retry_error:
                                    return ToolResult(
                                        error=f"输入文本失败：元素可能不可见或无法交互。错误: {str(retry_error)}。建议先使用get_state查看页面状态，或使用scroll_down滚动页面。"
                                    )
                            raise input_error
                    except Exception as e:
                        error_msg = str(e)
                        if "Timeout" in error_msg or "timeout" in error_msg:
                            return ToolResult(
                                error=f"操作超时：元素可能不可见或页面未完全加载。建议先使用get_state查看页面状态，或使用wait操作等待页面加载完成。"
                            )
                        elif "closed" in error_msg.lower():
                            return ToolResult(
                                error=f"浏览器已关闭。请重新打开页面。"
                            )
                        return ToolResult(error=f"输入文本失败: {error_msg}")

                # 滚动操作
                elif action == "scroll_down" or action == "scroll_up":
                    direction = 1 if action == "scroll_down" else -1
                    amount = scroll_amount if scroll_amount is not None else 500
                    await context.execute_javascript(
                        f"window.scrollBy(0, {direction * amount});"
                    )
                    return ToolResult(
                        output=f"已{'向下' if direction > 0 else '向上'}滚动{amount}像素"
                    )

                # 获取状态
                elif action == "get_state":
                    state = await context.get_state()
                    state_info = {
                        "url": state.url,
                        "title": state.title,
                        "interactive_elements": (
                            state.element_tree.clickable_elements_to_string()
                            if state.element_tree
                            else ""
                        ),
                    }
                    # 截屏
                    page = await context.get_current_page()
                    screenshot = await page.screenshot(
                        full_page=False, type="jpeg", quality=80
                    )
                    screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")

                    return ToolResult(
                        output=json.dumps(state_info, indent=2, ensure_ascii=False)
                    )

                # 等待操作
                elif action == "wait":
                    seconds_to_wait = seconds if seconds is not None else 3
                    await asyncio.sleep(seconds_to_wait)
                    return ToolResult(output=f"已等待{seconds_to_wait}秒")

                else:
                    return ToolResult(error=f"未知操作: {action}")

            except Exception as e:
                return ToolResult(error=f"浏览器操作'{action}'失败: {str(e)}")

    async def cleanup(self):
        """清理浏览器资源"""
        async with self.lock:
            if self.context is not None:
                await self.context.close()
                self.context = None
            if self.browser is not None:
                await self.browser.close()
                self.browser = None
