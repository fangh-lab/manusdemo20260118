import asyncio
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_workspace_basic():
    """测试workspace基本功能"""
    print("=" * 60)
    print("FanghaoManus Demo Workspace 快速测试")
    print("=" * 60)

    # 测试1: 检查workspace目录
    print("\n1. 检查workspace目录...")
    workspace_path = Path("workspace")
    if not workspace_path.exists():
        print("   ❌ workspace目录不存在，将自动创建")
    else:
        print(f"   ✅ workspace目录已存在: {workspace_path.absolute()}")

        # 列出workspace内容
        print("   工作区内容:")
        for item in workspace_path.iterdir():
            if item.is_dir():
                print(f"     📁 {item.name}/")
            else:
                print(f"     📄 {item.name}")

    # 测试2: 导入关键模块
    print("\n2. 测试模块导入...")
    try:
        from agent import Agent
        from tool.file import FileReadTool
        from tool.system import SystemInfoTool

        print("   ✅ 关键模块导入成功")
    except ImportError as e:
        print(f"   ❌ 模块导入失败: {e}")
        return False

    # 测试3: 创建工具实例
    print("\n3. 测试工具实例化...")
    try:
        file_read = FileReadTool()
        system_info = SystemInfoTool()
        print(f"   ✅ 工具实例化成功: {file_read.name}, {system_info.name}")
    except Exception as e:
        print(f"   ❌ 工具实例化失败: {e}")
        return False

    # 测试4: 测试文件读取
    print("\n4. 测试文件读取...")
    try:
        # 尝试读取README.md
        if Path("README.md").exists():
            result = await file_read.execute(path="README.md")
            if result.error:
                print(f"   ⚠️  文件读取错误: {result.error}")
            else:
                print(f"   ✅ 文件读取成功，内容长度: {len(result.output)}字符")
        else:
            print("   ℹ️  README.md文件不存在，跳过测试")
    except Exception as e:
        print(f"   ❌ 文件读取测试异常: {e}")

    # 测试5: 测试系统信息
    print("\n5. 测试系统信息...")
    try:
        result = await system_info.execute(info_type="platform")
        if result.error:
            print(f"   ⚠️  系统信息获取错误: {result.error}")
        else:
            print(f"   ✅ 系统信息获取成功")
            # 解析JSON输出
            import json

            try:
                info = json.loads(result.output)
                if "platform" in info:
                    print(f"     系统: {info['platform'].get('system', '未知')}")
                    print(
                        f"     Python版本: {info['platform'].get('python_version', '未知')}"
                    )
            except:
                print(f"     原始输出: {result.output[:100]}...")
    except Exception as e:
        print(f"   ❌ 系统信息测试异常: {e}")

    # 测试6: 检查依赖
    print("\n6. 检查依赖...")
    dependencies = [
        "pydantic",
        "openai",
        "browser-use",
        "tomli",
        "psutil",
        "aiohttp",
        "jsonpath_ng",
    ]
    missing = []

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            missing.append(dep)

    if missing:
        print(f"\n   ⚠️  缺少依赖: {', '.join(missing)}")
        print(f"   请运行: pip install {' '.join(missing)}")
    else:
        print(f"\n   ✅ 所有依赖已安装")

    # 测试7: 检查配置文件
    print("\n7. 检查配置文件...")
    config_path = Path("config/config.toml")
    if config_path.exists():
        print(f"   ✅ 配置文件存在: {config_path}")

        # 检查基本配置
        try:
            import tomli

            with open(config_path, "rb") as f:
                config = tomli.load(f)

            if "llm" in config:
                llm_config = config["llm"]
                print(f"     模型: {llm_config.get('model', '未设置')}")
                print(f"     API类型: {llm_config.get('api_type', '未设置')}")

                # 检查API密钥
                api_key = llm_config.get("api_key", "")
                if api_key and api_key != "YOUR_API_KEY":
                    print(f"     API密钥: 已设置（{len(api_key)}字符）")
                else:
                    print(f"     ⚠️  API密钥: 需要设置（当前: {api_key}）")
            else:
                print(f"     ⚠️  缺少llm配置")

        except Exception as e:
            print(f"     ❌ 配置文件解析错误: {e}")
    else:
        print(f"   ❌ 配置文件不存在: {config_path}")
        print(f"     请创建 config/config.toml 文件")

    print("\n" + "=" * 60)
    print("快速测试完成")
    print("=" * 60)

    return True


async def test_main_program():
    """测试主程序启动"""
    print("\n" + "=" * 60)
    print("测试主程序启动")
    print("=" * 60)

    print("启动命令: python main.py")
    print("\n预期行为:")
    print("1. 显示程序标题和版本信息")
    print("2. 自动创建workspace目录（如果不存在）")
    print("3. 加载所有工具（浏览器、文件、系统、数据、网络）")
    print("4. 显示工作区信息")
    print("5. 进入交互模式")
    print("\n交互示例:")
    print("👤 你: 创建一个测试文件")
    print("🤔 思考中...")
    print("🛠️  执行工具：workspace_file_write")
    print("📝 文件将保存到工作区: workspace\\files\\test.txt")
    print("✅  工具执行成功")
    print("🤖 助手: 成功写入文件")

    print("\n" + "=" * 60)
    print("要运行主程序，请执行:")
    print("python main.py")
    print("=" * 60)

    return True


def create_workspace_structure():
    """创建workspace目录结构"""
    print("\n创建workspace目录结构...")

    workspace_path = Path("workspace")
    subdirs = ["files", "logs", "data", "outputs", "temp"]

    # 创建workspace目录
    if not workspace_path.exists():
        workspace_path.mkdir()
        print(f"✅ 创建workspace目录: {workspace_path.absolute()}")
    else:
        print(f"✅ workspace目录已存在: {workspace_path.absolute()}")

    # 创建子目录
    created_count = 0
    for subdir in subdirs:
        subdir_path = workspace_path / subdir
        if not subdir_path.exists():
            subdir_path.mkdir()
            created_count += 1

    if created_count > 0:
        print(f"✅ 创建 {created_count} 个子目录: {', '.join(subdirs)}")
    else:
        print(f"✅ 所有子目录已存在")

    # 创建示例文件
    example_file = workspace_path / "files" / "example.txt"
    if not example_file.exists():
        example_file.write_text("这是一个示例文件\n由FanghaoManus Demo创建\n")
        print(f"✅ 创建示例文件: {example_file}")

    # 显示目录结构
    print("\nworkspace目录结构:")
    for item in workspace_path.rglob("*"):
        indent = "  " * (len(item.relative_to(workspace_path).parts) - 1)
        if item.is_dir():
            print(f"{indent}📁 {item.name}/")
        else:
            size = item.stat().st_size
            print(f"{indent}📄 {item.name} ({size}字节)")

    return True


async def main():
    """主测试函数"""
    print("🚀 FanghaoManus Demo Workspace 环境测试")

    # 创建workspace目录结构
    create_workspace_structure()

    # 运行基本测试
    await test_workspace_basic()

    # 测试主程序启动
    await test_main_program()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 确保config/config.toml中的API密钥已设置")
    print("2. 运行主程序: python main.py")
    print("3. 使用测试用例进行功能验证")
    print("4. 所有生成的文件将自动保存到workspace目录")
    print("\n祝您测试顺利！🎉")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试发生异常: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
