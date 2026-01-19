import json
import re
from typing import Any, Dict, List, Optional

try:
    from jsonpath_ng import parse

    HAS_JSONPATH = True
except ImportError:
    HAS_JSONPATH = False

from tool.base import BaseTool, ToolResult


class JsonTool(BaseTool):
    """JSON处理工具"""

    name: str = "json_process"
    description: str = "处理JSON数据（解析、验证、查询、格式化）"
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["parse", "stringify", "validate", "query", "format"],
                "description": "操作类型",
            },
            "data": {"type": "string", "description": "JSON数据或Python对象字符串"},
            "query": {
                "type": "string",
                "description": "JSONPath查询表达式（仅query操作需要）",
            },
            "indent": {
                "type": "integer",
                "description": "格式化缩进空格数",
                "default": 2,
            },
        },
        "required": ["action", "data"],
    }

    async def execute(
        self, action: str, data: str, query: Optional[str] = None, indent: int = 2
    ) -> ToolResult:
        try:
            if action == "parse":
                # 解析JSON字符串
                try:
                    parsed = json.loads(data)
                    formatted = json.dumps(parsed, indent=indent, ensure_ascii=False)
                    return ToolResult(output=f"JSON解析成功：\n{formatted}")
                except json.JSONDecodeError as e:
                    return ToolResult(
                        error=f"JSON解析失败：{str(e)}\n位置：第{e.lineno}行，第{e.colno}列"
                    )

            elif action == "stringify":
                # 将Python对象字符串转换为JSON
                try:
                    # 尝试解析为Python对象
                    import ast

                    obj = ast.literal_eval(data)
                    json_str = json.dumps(obj, indent=indent, ensure_ascii=False)
                    return ToolResult(output=f"JSON字符串化成功：\n{json_str}")
                except (SyntaxError, ValueError) as e:
                    return ToolResult(error=f"Python对象解析失败：{str(e)}")

            elif action == "validate":
                # 验证JSON格式
                try:
                    json.loads(data)
                    return ToolResult(output="✅ JSON格式有效")
                except json.JSONDecodeError as e:
                    return ToolResult(
                        error=f"❌ JSON格式无效：{str(e)}\n位置：第{e.lineno}行，第{e.colno}列"
                    )

            elif action == "query":
                # 使用JSONPath查询
                if not HAS_JSONPATH:
                    return ToolResult(
                        error="需要安装jsonpath-ng库：pip install jsonpath-ng"
                    )

                if not query:
                    return ToolResult(error="query操作需要query参数")

                try:
                    # 解析JSON数据
                    json_data = json.loads(data)

                    # 解析JSONPath表达式
                    jsonpath_expr = parse(query)

                    # 执行查询
                    matches = []
                    for match in jsonpath_expr.find(json_data):
                        matches.append(
                            {"value": match.value, "path": str(match.full_path)}
                        )

                    if not matches:
                        return ToolResult(output="未找到匹配项")

                    # 格式化输出
                    result = {
                        "query": query,
                        "match_count": len(matches),
                        "matches": matches,
                    }

                    formatted = json.dumps(result, indent=indent, ensure_ascii=False)
                    return ToolResult(output=f"JSONPath查询结果：\n{formatted}")

                except Exception as e:
                    return ToolResult(error=f"JSONPath查询失败：{str(e)}")

            elif action == "format":
                # 格式化JSON
                try:
                    parsed = json.loads(data)
                    formatted = json.dumps(
                        parsed, indent=indent, sort_keys=True, ensure_ascii=False
                    )
                    return ToolResult(output=f"JSON格式化成功：\n{formatted}")
                except json.JSONDecodeError as e:
                    return ToolResult(error=f"JSON格式化失败：{str(e)}")

            else:
                return ToolResult(error=f"未知操作：{action}")

        except Exception as e:
            return ToolResult(error=f"JSON处理失败：{str(e)}")


class TextTool(BaseTool):
    """文本处理工具"""

    name: str = "text_process"
    description: str = "文本处理（统计、搜索、替换、分割、格式化）"
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "count",
                    "search",
                    "replace",
                    "split",
                    "join",
                    "format",
                    "case",
                ],
                "description": "操作类型",
            },
            "text": {"type": "string", "description": "输入文本"},
            "pattern": {"type": "string", "description": "搜索/替换模式（正则表达式）"},
            "replacement": {"type": "string", "description": "替换文本"},
            "separator": {
                "type": "string",
                "description": "分隔符（split/join操作使用）",
            },
            "case_type": {
                "type": "string",
                "enum": ["lower", "upper", "title", "capitalize"],
                "description": "大小写转换类型",
            },
            "format_args": {"type": "string", "description": "格式化参数（JSON格式）"},
        },
        "required": ["action", "text"],
    }

    async def execute(self, action: str, text: str, **kwargs) -> ToolResult:
        try:
            if action == "count":
                # 统计文本信息
                lines = text.splitlines()
                words = text.split()

                result = {
                    "字符数": len(text),
                    "字节数": len(text.encode("utf-8")),
                    "单词数": len(words),
                    "行数": len(lines),
                    "非空行数": len([line for line in lines if line.strip()]),
                    "最长行长度": max(len(line) for line in lines) if lines else 0,
                }

                formatted = json.dumps(result, indent=2, ensure_ascii=False)
                return ToolResult(output=f"文本统计结果：\n{formatted}")

            elif action == "search":
                # 正则表达式搜索
                pattern = kwargs.get("pattern", "")
                if not pattern:
                    return ToolResult(error="search操作需要pattern参数")

                try:
                    matches = list(re.finditer(pattern, text))
                    if not matches:
                        return ToolResult(output="未找到匹配项")

                    result = []
                    for i, match in enumerate(matches, 1):
                        result.append(
                            {
                                "序号": i,
                                "匹配文本": match.group(),
                                "起始位置": match.start(),
                                "结束位置": match.end(),
                                "匹配组": match.groups() if match.groups() else None,
                            }
                        )

                    formatted = json.dumps(result, indent=2, ensure_ascii=False)
                    return ToolResult(
                        output=f"搜索到 {len(matches)} 个匹配项：\n{formatted}"
                    )

                except re.error as e:
                    return ToolResult(error=f"正则表达式错误：{str(e)}")

            elif action == "replace":
                # 正则表达式替换
                pattern = kwargs.get("pattern", "")
                replacement = kwargs.get("replacement", "")

                if not pattern:
                    return ToolResult(error="replace操作需要pattern参数")

                try:
                    result = re.sub(pattern, replacement, text)
                    return ToolResult(output=f"替换结果：\n{result}")
                except re.error as e:
                    return ToolResult(error=f"正则表达式错误：{str(e)}")

            elif action == "split":
                # 分割文本
                separator = kwargs.get("separator", None)

                if separator:
                    parts = text.split(separator)
                else:
                    # 默认按空白字符分割
                    parts = re.split(r"\s+", text.strip())

                result = {
                    "分割符": separator if separator else "空白字符",
                    "部分数量": len(parts),
                    "各部分": parts,
                }

                formatted = json.dumps(result, indent=2, ensure_ascii=False)
                return ToolResult(output=f"分割结果：\n{formatted}")

            elif action == "join":
                # 连接文本（假设text是JSON数组）
                separator = kwargs.get("separator", " ")

                try:
                    items = json.loads(text)
                    if not isinstance(items, list):
                        return ToolResult(error="输入必须是JSON数组")

                    result = separator.join(str(item) for item in items)
                    return ToolResult(output=f"连接结果：\n{result}")
                except json.JSONDecodeError:
                    # 如果不是JSON，尝试按行分割
                    lines = text.splitlines()
                    result = separator.join(lines)
                    return ToolResult(output=f"连接结果：\n{result}")

            elif action == "format":
                # 字符串格式化
                format_args = kwargs.get("format_args", "{}")

                try:
                    args = json.loads(format_args)
                    if not isinstance(args, dict):
                        return ToolResult(error="format_args必须是JSON对象")

                    result = text.format(**args)
                    return ToolResult(output=f"格式化结果：\n{result}")
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    return ToolResult(error=f"格式化失败：{str(e)}")

            elif action == "case":
                # 大小写转换
                case_type = kwargs.get("case_type", "lower")

                if case_type == "lower":
                    result = text.lower()
                elif case_type == "upper":
                    result = text.upper()
                elif case_type == "title":
                    result = text.title()
                elif case_type == "capitalize":
                    result = text.capitalize()
                else:
                    return ToolResult(error=f"不支持的大小写类型：{case_type}")

                return ToolResult(output=f"大小写转换结果：\n{result}")

            else:
                return ToolResult(error=f"未知操作：{action}")

        except Exception as e:
            return ToolResult(error=f"文本处理失败：{str(e)}")


class MathTool(BaseTool):
    """数学计算工具"""

    name: str = "math_calculate"
    description: str = "数学计算（基本运算、统计、单位转换）"
    parameters: dict = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式或计算类型"},
            "operation": {
                "type": "string",
                "enum": ["eval", "statistics", "convert", "geometry"],
                "description": "操作类型",
                "default": "eval",
            },
            "numbers": {
                "type": "string",
                "description": "数字列表（JSON格式，用于统计）",
            },
            "from_unit": {"type": "string", "description": "源单位"},
            "to_unit": {"type": "string", "description": "目标单位"},
            "value": {"type": "number", "description": "要转换的数值"},
        },
        "required": ["expression"],
    }

    async def execute(self, expression: str, **kwargs) -> ToolResult:
        try:
            operation = kwargs.get("operation", "eval")

            if operation == "eval":
                # 计算数学表达式
                try:
                    # 安全计算：只允许数学运算
                    allowed_chars = set("0123456789+-*/(). ")
                    if not all(c in allowed_chars for c in expression):
                        return ToolResult(error="表达式包含非法字符")

                    # 使用eval计算（有限制）
                    result = eval(expression, {"__builtins__": {}}, {})
                    return ToolResult(output=f"计算结果：{expression} = {result}")
                except Exception as e:
                    return ToolResult(error=f"计算失败：{str(e)}")

            elif operation == "statistics":
                # 统计计算
                numbers_str = kwargs.get("numbers", "[]")
                try:
                    numbers = json.loads(numbers_str)
                    if not isinstance(numbers, list):
                        return ToolResult(error="numbers必须是JSON数组")

                    if not numbers:
                        return ToolResult(error="数字列表不能为空")

                    import statistics

                    stats = {
                        "数据": numbers,
                        "数量": len(numbers),
                        "总和": sum(numbers),
                        "平均值": statistics.mean(numbers),
                        "中位数": statistics.median(numbers),
                        "最小值": min(numbers),
                        "最大值": max(numbers),
                        "标准差": statistics.stdev(numbers) if len(numbers) > 1 else 0,
                    }

                    formatted = json.dumps(stats, indent=2, ensure_ascii=False)
                    return ToolResult(output=f"统计结果：\n{formatted}")

                except (json.JSONDecodeError, statistics.StatisticsError) as e:
                    return ToolResult(error=f"统计计算失败：{str(e)}")

            elif operation == "convert":
                # 单位转换
                from_unit = kwargs.get("from_unit", "")
                to_unit = kwargs.get("to_unit", "")
                value = kwargs.get("value", 0)

                if not from_unit or not to_unit:
                    return ToolResult(error="单位转换需要from_unit和to_unit参数")

                # 简单的单位转换表
                conversions = {
                    # 长度
                    ("m", "km"): 0.001,
                    ("km", "m"): 1000,
                    ("m", "cm"): 100,
                    ("cm", "m"): 0.01,
                    ("inch", "cm"): 2.54,
                    ("cm", "inch"): 0.3937,
                    ("feet", "m"): 0.3048,
                    ("m", "feet"): 3.28084,
                    # 重量
                    ("kg", "g"): 1000,
                    ("g", "kg"): 0.001,
                    ("kg", "lb"): 2.20462,
                    ("lb", "kg"): 0.453592,
                    # 温度（特殊处理）
                    ("c", "f"): lambda x: x * 9 / 5 + 32,
                    ("f", "c"): lambda x: (x - 32) * 5 / 9,
                    ("c", "k"): lambda x: x + 273.15,
                    ("k", "c"): lambda x: x - 273.15,
                    # 时间
                    ("s", "min"): 1 / 60,
                    ("min", "s"): 60,
                    ("min", "hour"): 1 / 60,
                    ("hour", "min"): 60,
                    ("hour", "day"): 1 / 24,
                    ("day", "hour"): 24,
                }

                key = (from_unit.lower(), to_unit.lower())

                if key in conversions:
                    converter = conversions[key]
                    if callable(converter):
                        result = converter(value)
                    else:
                        result = value * converter

                    return ToolResult(
                        output=f"单位转换：{value} {from_unit} = {result:.4f} {to_unit}"
                    )
                else:
                    return ToolResult(
                        error=f"不支持的单位转换：{from_unit} → {to_unit}"
                    )

            elif operation == "geometry":
                # 几何计算
                import math

                if expression == "circle_area":
                    radius = kwargs.get("value", 0)
                    area = math.pi * radius**2
                    return ToolResult(output=f"圆面积（半径={radius}）= {area:.4f}")

                elif expression == "rectangle_area":
                    # 假设value是"长,宽"格式
                    dims = str(kwargs.get("value", "0,0")).split(",")
                    if len(dims) != 2:
                        return ToolResult(error="矩形面积需要长和宽，格式：长,宽")

                    length, width = float(dims[0]), float(dims[1])
                    area = length * width
                    return ToolResult(
                        output=f"矩形面积（长={length}, 宽={width}）= {area:.4f}"
                    )

                elif expression == "triangle_area":
                    # 假设value是"底,高"格式
                    dims = str(kwargs.get("value", "0,0")).split(",")
                    if len(dims) != 2:
                        return ToolResult(error="三角形面积需要底和高，格式：底,高")

                    base, height = float(dims[0]), float(dims[1])
                    area = 0.5 * base * height
                    return ToolResult(
                        output=f"三角形面积（底={base}, 高={height}）= {area:.4f}"
                    )

                else:
                    return ToolResult(error=f"不支持的几何计算：{expression}")

            else:
                return ToolResult(error=f"未知操作：{operation}")

        except Exception as e:
            return ToolResult(error=f"数学计算失败：{str(e)}")
