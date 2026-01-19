import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("最小导入测试")
print("=" * 60)

try:
    # 测试1: 导入ToolResult
    print("1. 测试导入ToolResult...")
    from tool.base import ToolResult

    print("   ✅ ToolResult导入成功")

    # 测试2: 创建ToolResult实例
    print("2. 测试创建ToolResult实例...")
    result = ToolResult(output="测试成功")
    print(f"   ✅ ToolResult实例创建成功: {result}")

    # 测试3: 测试错误结果
    error_result = ToolResult(error="测试错误")
    print(f"   ✅ 错误ToolResult创建成功: {error_result}")

    # 测试4: 测试字符串表示
    print("3. 测试字符串表示...")
    print(f"   ✅ 成功结果字符串: {str(result)}")
    print(f"   ✅ 错误结果字符串: {str(error_result)}")

    print("\n" + "=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)

except ImportError as e:
    print(f"❌ 导入失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
