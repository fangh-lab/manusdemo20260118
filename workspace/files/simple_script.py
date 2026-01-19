#!/usr/bin/env python3
"""
一个简单的Python脚本示例
演示基本功能：变量、循环、函数、文件操作
"""

def greet(name):
    """问候函数"""
    return f"你好，{name}！欢迎使用Python。"

def calculate_sum(numbers):
    """计算列表数字的和"""
    return sum(numbers)

def main():
    """主函数"""
    print("=== Python脚本示例 ===")
    
    # 1. 基本变量和字符串
    name = "用户"
    print(greet(name))
    
    # 2. 列表和循环
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    print(f"\n数字列表: {numbers}")
    
    # 3. 计算总和
    total = calculate_sum(numbers)
    print(f"数字总和: {total}")
    
    # 4. 条件判断
    if total > 30:
        print("总和大于30")
    else:
        print("总和小于等于30")
    
    # 5. 循环示例
    print("\n循环示例:")
    for i, num in enumerate(numbers, 1):
        print(f"第{i}个数字: {num}")
    
    # 6. 字典示例
    print("\n字典示例:")
    student = {
        "name": "张三",
        "age": 20,
        "courses": ["数学", "物理", "编程"]
    }
    print(f"学生信息: {student}")
    
    # 7. 文件操作示例
    print("\n文件操作示例:")
    try:
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(f"脚本执行结果:\n")
            f.write(f"数字列表: {numbers}\n")
            f.write(f"总和: {total}\n")
            f.write(f"执行时间: {datetime.now()}\n")
        print("结果已保存到 output.txt")
    except Exception as e:
        print(f"文件保存失败: {e}")
    
    print("\n=== 脚本执行完成 ===")

if __name__ == "__main__":
    from datetime import datetime
    main()