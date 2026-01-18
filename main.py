"""主入口文件"""
import asyncio
import sys
from pathlib import Path

# 确保可以导入模块
sys.path.insert(0, str(Path(__file__).parent))

from agent import Agent
from tool.browser import BrowserTool


async def main():
    """主函数"""
    print("=" * 50)
    print("FanghaoManus Demo - 简化版智能体")
    print("=" * 50)

    # 创建浏览器工具
    browser_tool = BrowserTool()

    # 创建智能体
    agent = Agent(
        tools=[browser_tool],
        system_prompt="你是一个可以帮助用户浏览网页的AI助手。你可以使用浏览器工具来导航网页、点击元素、输入文本等。",
    )

    try:
        # 交互式循环
        while True:
            user_input = input("\n你: ")

            if user_input.lower() in ["exit", "quit", "退出"]:
                print("再见！")
                break

            if not user_input.strip():
                continue

            print("\n思考中...")
            result = await agent.run(user_input, max_steps=10)
            print(f"\n助手: {result}")

    except KeyboardInterrupt:
        print("\n\n程序被中断")
    finally:
        # 清理资源
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
