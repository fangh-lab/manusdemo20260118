# FanghaoManus Demo - 增强版智能体项目

基于 OpenManus 设计的简化版智能体系统，专注于核心功能：**记忆管理**和**工具调用**。

## 📋 项目概述

这是一个功能丰富的智能体实现，包含：

- ✅ **记忆模块（Memory）**：管理对话历史
- ✅ **工具系统（Tools）**：浏览器、文件、系统、数据、网络等20+工具
- ✅ **智能体（Agent）**：集成LLM和工具调用，支持权限控制和统计
- ✅ **配置系统**：支持多种LLM API
- ✅ **安全机制**：全面的安全检查和限制

## 🏗️ 项目结构

```
fanghaomanusdemo/
├── config.py              # 配置加载模块
├── memory.py              # 记忆模块
├── llm.py                 # LLM封装模块
├── agent.py               # 智能体模块（增强版）
├── main.py                # 主入口文件（增强版）
├── test_new_tools.py      # 新工具测试脚本
├── tool/                  # 工具目录
│   ├── __init__.py
│   ├── base.py            # 工具基类
│   ├── browser.py         # 浏览器工具
│   ├── file.py            # 文件操作工具
│   ├── system.py          # 系统操作工具
│   ├── data.py            # 数据处理工具
│   └── network.py         # 网络工具
├── config/                # 配置文件目录
│   └── config.toml        # 配置文件
└── 文档文件/
    ├── 新工具使用示例.md      # 新工具详细使用示例
    ├── 项目综合分析报告.md    # 完整项目分析
    ├── 项目执行摘要.md       # 项目快速参考
    ├── 项目健康度检查报告.md  # 项目状态评估
    ├── 项目维护指南.md       # 维护和开发指南
    └── 技术架构图.md        # 架构设计说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

编辑 `config/config.toml`，设置你的LLM API密钥：

```toml
[llm]
model = "gpt-4o-mini"
api_key = "YOUR_API_KEY"  # 替换为你的API密钥
base_url = "https://api.openai.com/v1/"
```

### 3. 运行项目

```bash
# 运行增强版主程序
python main.py

# 测试新工具
python test_new_tools.py --quick
python test_new_tools.py --full
```

### 4. 使用示例

```
你: 帮我打开百度首页
助手: 正在打开百度首页...

你: 读取README.md文件
助手: 使用file_read工具读取文件...

你: 查看系统信息
助手: 使用system_info工具获取信息...

你: 计算圆的面积，半径是5
助手: 使用math_calculate工具计算...
```

## 🛠️ 新增工具系统详解

### 1. 文件操作工具

**位置**: `tool/file.py`

**包含工具**：
- `file_read`: 读取文件内容（10MB限制）
- `file_write`: 写入内容到文件（5MB限制）
- `directory_list`: 列出目录内容（支持递归和隐藏文件）

**使用示例**：
```python
# 读取文件
result = await file_read.execute(path="README.md")

# 写入文件
result = await file_write.execute(path="test.txt", content="Hello World")

# 列出目录
result = await directory_list.execute(path=".", recursive=True)
```

### 2. 系统操作工具

**位置**: `tool/system.py`

**包含工具**：
- `command_execute`: 执行系统命令（安全限制，禁止危险命令）
- `system_info`: 获取系统信息（CPU、内存、磁盘、网络等）
- `python_execute`: 执行Python代码（安全沙箱环境）

**安全特性**：
- 危险命令过滤（rm、format、shutdown等）
- 超时限制（默认30秒）
- 输出长度限制

### 3. 数据处理工具

**位置**: `tool/data.py`

**包含工具**：
- `json_process`: JSON处理（解析、验证、查询、格式化）
- `text_process`: 文本处理（统计、搜索、替换、分割、格式化）
- `math_calculate`: 数学计算（基本运算、统计、单位转换、几何计算）

### 4. 网络工具

**位置**: `tool/network.py`

**包含工具**：
- `http_request`: 发送HTTP请求（GET、POST、PUT、DELETE等）
- `network_test`: 网络测试（Ping、TCP连接、HTTP测试、DNS解析）
- `websocket`: WebSocket连接和消息发送

## 📚 核心模块详解

### 5. 记忆模块（Memory）

**位置**: `memory.py`

**设计说明**：

记忆模块负责管理对话历史，采用**消息序列**的方式存储：

```
[System] → [User] → [Assistant] → [Tool] → [User] → ...
```

**核心特性**：

1. **消息类型**：
   - `system`: 系统提示词
   - `user`: 用户消息
   - `assistant`: 助手回复
   - `tool`: 工具执行结果

2. **消息限制**：
   - 默认最多保留100条消息
   - 自动保留第一个system消息
   - 超过限制时保留最新的消息

3. **使用示例**：

```python
from memory import Memory, Message

memory = Memory()
memory.add_message(Message.user_message("你好"))
memory.add_message(Message.assistant_message("你好！有什么可以帮你的吗？"))

# 获取所有消息
messages = memory.to_dict_list()
```

**为什么这样设计**：

- ✅ **保持上下文**：完整保存对话历史，LLM可以理解上下文
- ✅ **工具结果追踪**：通过`tool_call_id`关联工具调用和结果
- ✅ **自动管理**：限制消息数量，防止上下文过长导致API费用过高

### 6. 工具系统（Tools）

#### 6.1 工具基类（BaseTool）

**位置**: `tool/base.py`

所有工具都继承自 `BaseTool`：

```python
class BaseTool(ABC, BaseModel):
    name: str              # 工具名称
    description: str       # 工具描述
    parameters: dict       # 参数schema（JSON Schema格式）

    async def execute(self, **kwargs) -> ToolResult:
        """执行工具逻辑"""
        pass

    def to_param(self) -> Dict:
        """转换为OpenAI函数调用格式"""
        pass
```

#### 6.2 浏览器工具（BrowserTool）

**位置**: `tool/browser.py`

**支持的操作**：

| 操作 | 参数 | 说明 |
|------|------|------|
| `go_to_url` | `url` | 导航到指定URL |
| `click_element` | `index` | 点击指定索引的元素 |
| `input_text` | `index`, `text` | 在指定元素中输入文本 |
| `scroll_down` | `scroll_amount` | 向下滚动 |
| `scroll_up` | `scroll_amount` | 向上滚动 |
| `go_back` | - | 返回上一页 |
| `get_state` | - | 获取当前页面状态 |
| `wait` | `seconds` | 等待指定秒数 |

**使用示例**：

```python
from tool.browser import BrowserTool

browser = BrowserTool()

# 导航到网页
result = await browser.execute(action="go_to_url", url="https://www.baidu.com")

# 获取页面状态
result = await browser.execute(action="get_state")
```

**工具如何工作**：

1. **工具定义**：通过 `to_param()` 转换为OpenAI格式
2. **传递给LLM**：LLM根据任务选择合适的工具
3. **执行工具**：Agent解析LLM返回的tool_calls，执行对应工具
4. **返回结果**：工具结果返回给LLM，继续对话

### 7. 智能体（Agent） - 增强版

**位置**: `agent.py`

**新增特性**：
- 工具使用统计（调用次数、成功率、平均时间）
- 权限控制（allowed_tools参数）
- 使用次数限制（max_tool_usage参数）
- 详细的统计信息获取

**工作流程**：

```
用户输入
    ↓
添加用户消息到Memory
    ↓
循环（最多max_steps次）:
    ├─ 思考（Think）: LLM分析当前状态，决定下一步
    │   └─ 可能返回: 文本回复 或 工具调用请求
    │
    └─ 行动（Act）: 如果有工具调用，执行工具
        └─ 将工具结果添加到Memory
    ↓
返回最终结果
```

**核心方法**：

- `run(user_input, max_steps)`: 主运行方法
- `_think()`: 调用LLM进行思考
- `_act(tool_calls)`: 执行工具调用

**使用示例**：

```python
from agent import Agent
from tool.browser import BrowserTool

# 创建工具
browser_tool = BrowserTool()

# 创建智能体
agent = Agent(
    tools=[browser_tool],
    system_prompt="你是一个浏览器助手...",
)

# 运行
result = await agent.run("打开百度")
```

### 8. LLM封装

**位置**: `llm.py`

**支持的API类型**：

- `openai`: OpenAI API（包括兼容的API如Ollama）
- `azure`: Azure OpenAI
- `anthropic`: Anthropic Claude API
- `ollama`: 本地Ollama

**核心方法**：

- `ask(messages)`: 普通对话（不使用工具）
- `ask_tool(messages, tools)`: 带工具调用的对话

### 9. 配置系统

**位置**: `config.py` 和 `config/config.toml`

**配置文件格式**：

```toml
[llm]
model = "gpt-4o-mini"
api_key = "YOUR_API_KEY"
base_url = "https://api.openai.com/v1/"
max_tokens = 4096
temperature = 0.7
api_type = "openai"

[browser]
headless = false
disable_security = true
```

**如何切换LLM**：

1. **OpenAI**: 默认配置即可
2. **Azure OpenAI**: 修改`api_type = "azure"`，添加`api_version`
3. **Ollama**: 修改`api_type = "ollama"`，设置`base_url = "http://localhost:11434/v1"`
4. **Anthropic**: 修改`api_type = "anthropic"`，使用Claude模型

## 🔄 工具调用流程详解

### 完整流程示例（增强版）

```
1. 用户输入: "读取README.md文件，然后统计行数"

2. Agent.run() 添加用户消息到Memory，检查工具使用次数

3. _think() 调用LLM（包含工具统计信息）:
   - 传入: 对话历史 + 所有工具定义
   - LLM分析: 需要先读取文件，再处理文本
   - LLM返回两个tool_calls:
     [
       {
         "id": "call_123",
         "function": {
           "name": "file_read",
           "arguments": '{"path": "README.md"}'
         }
       },
       {
         "id": "call_124",
         "function": {
           "name": "text_process",
           "arguments": '{"action": "count", "text": "[文件内容]"}'
         }
       }
     ]

4. _act() 执行工具（带统计）:
   - 解析 tool_calls
   - 执行 file_read.execute(path="README.md")，记录执行时间和结果
   - 执行 text_process.execute(action="count", text="...")，记录执行时间和结果
   - 更新工具使用统计

5. 继续循环:
   - LLM看到工具执行结果
   - 决定是否需要进一步处理
   - 继续执行工具...

6. 最终LLM返回文本回复，循环结束
```

### 工具调用的关键点（增强版）

1. **工具定义传递给LLM**：
   ```python
   tools = [tool.to_param() for tool in self.tools]
   # 转换为OpenAI格式：
   # [{
   #   "type": "function",
   #   "function": {
   #     "name": "browser",
   #     "description": "...",
   #     "parameters": {...}
   #   }
   # }]
   ```

2. **LLM返回工具调用**：
   ```python
   response.tool_calls = [{
     "id": "call_123",
     "function": {
       "name": "browser",
       "arguments": '{"action": "go_to_url", "url": "..."}'
     }
   }]
   ```

3. **执行工具并返回结果**：
   ```python
   # 执行工具
   result = await tool.execute(**args)

   # 返回给LLM
   tool_msg = Message.tool_message(
     content=str(result),
     tool_call_id=tool_call.id,
     name=tool_name
   )
   memory.add_message(tool_msg)
   ```

## 💡 与OpenManus的区别

| 特性 | OpenManus | FanghaoManus Demo 增强版 |
|------|-----------|--------------------------|
| **规划功能** | ✅ 完整的PlanningFlow | ⚠️ 简化版（Think-Act循环） |
| **工具数量** | 20+ 工具 | ✅ 20+ 工具（浏览器、文件、系统、数据、网络） |
| **记忆功能** | 完整的Memory系统 | ✅ 增强版Memory（带统计和权限控制） |
| **配置系统** | 复杂，支持多环境 | ✅ 简化版配置（易于使用） |
| **安全机制** | 完整的安全系统 | ✅ 全面的安全检查（命令过滤、文件限制、网络限制） |
| **代码复杂度** | 高（多层抽象） | 中等（结构清晰，易于扩展） |

## 🔧 扩展开发

### 添加新工具

项目已经提供了完整的工具扩展框架，新增了20+工具：

1. **查看现有工具示例**：
   - `tool/file.py` - 文件操作工具示例
   - `tool/system.py` - 系统操作工具示例
   - `tool/data.py` - 数据处理工具示例
   - `tool/network.py` - 网络工具示例

2. **创建新工具类**（继承BaseTool）：

```python
# tool/my_tool.py
from tool.base import BaseTool, ToolResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "我的工具描述"
    parameters = {
        "type": "object",
        "properties": {
            "param1": {"type": "string"}
        },
        "required": ["param1"]
    }

    async def execute(self, param1: str) -> ToolResult:
        # 实现工具逻辑（记得添加安全检查）
        return ToolResult(output="执行结果")
```

3. **注册到Agent**：

```python
from tool.my_tool import MyTool

agent = Agent(tools=[browser_tool, file_read_tool, MyTool()])
```

### 权限控制

```python
# 只允许特定的工具
agent = Agent(
    tools=all_tools,
    allowed_tools=["file_read", "system_info", "http_request"],
    max_tool_usage=50  # 限制工具使用次数
)
```

### 修改记忆策略

编辑 `memory.py` 中的 `Memory.add_message()` 方法，可以自定义消息管理策略。

## 📝 注意事项

1. **API密钥安全**：不要将包含真实API密钥的配置文件提交到版本控制
2. **资源管理**：使用完工具后记得调用 `agent.cleanup()` 释放资源
3. **安全限制**：所有工具都有安全限制，请

## 🐛 常见问题与错误分析（增强版）

### Q: 如何查看浏览器操作过程？

A: 在`config.toml`中设置 `headless = false`，浏览器窗口会显示出来。

### Q: 支持哪些LLM？

A: 支持OpenAI兼容的API，包括OpenAI、Azure OpenAI、Ollama等。Anthropic需要特殊处理。

### Q: 如何添加更多工具？

A: 参考"扩展开发"章节，创建新的工具类并注册到Agent。

### Q: 记忆模块如何工作？

A: 记忆模块维护一个消息列表，每次对话都会添加到列表中。LLM可以看到完整的对话历史。

### Q: 遇到"元素定位超时"错误怎么办？

**错误信息：**
```
ERROR [browser] Failed to locate element: ElementHandle.scroll_into_view_if_needed: Timeout 30000ms exceeded.
element is not visible
```

**重要说明：**
- ⚠️ 这是 `browser-use` 库内部的警告
- ✅ **即使出现这个警告，操作最终可能成功**
- 📝 库内部有重试机制，会尝试多种方式操作元素

**原因分析：**
1. **页面未完全加载**：在页面加载完成前就尝试操作元素
2. **元素索引错误**：选择的元素索引可能不正确
3. **元素不可见**：元素被遮挡或需要滚动才能看到
4. **滚动超时**：库尝试滚动元素到视图时超时（但可能通过其他方式成功）

**解决方案：**

**方案1：优化操作流程（推荐）**
**示例流程（复杂任务）：**
```
用户: 获取天气数据并生成报告

→ Agent: http_request (获取天气API数据)
→ Agent: json_process (解析JSON响应)
→ Agent: text_process (提取温度信息)
→ Agent: math_calculate (计算平均温度)
→ Agent: file_write (保存报告到文件)
→ Agent: system_info (记录系统资源使用情况)

统计信息：
- 总工具调用：6次
- 成功率：100%
- 总执行时间：2.3秒
```

**方案2：如果警告不影响结果**
- 如果最终操作成功，可以忽略警告
- 代码已包含自动滚动重试机制
- 建议优化操作流程以减少警告

**方案3：手动处理**
- 如果操作失败，查看错误信息
- 按照建议使用 `get_state` 查看页面状态
- 使用 `wait` 等待页面加载
- 使用 `scroll_down` 滚动页面

**详细说明：** 参考 `错误处理说明.md`

### Q: 遇到"浏览器已关闭"错误怎么办？

**错误信息：**
```
Target page, context or browser has been closed
```

**解决方案：**
1. 重新打开页面：使用 `go_to_url` 重新导航
2. 检查浏览器状态：确保浏览器实例正常运行
3. 如果问题持续，重启程序

### Q: API调用超时怎么办？

**错误信息：**
```
openai.APITimeoutError: Request timed out
```

**解决方案：**
1. 检查网络连接
2. 检查 `base_url` 配置（必须包含 `/v1` 路径）
3. 检查API密钥是否有效
4. 代码已包含自动重试机制（最多3次）

### Q: 新工具执行失败怎么办？

**常见错误及解决方案：**

1. **文件工具错误**：
   - "文件不存在"：检查文件路径是否正确
   - "文件过大"：文件超过10MB限制，请分割文件
   - "编码错误"：尝试指定正确的编码格式

2. **系统工具错误**：
   - "禁止执行危险命令"：命令包含危险操作，请修改命令
   - "命令执行超时"：命令执行时间过长，请优化命令或增加超时时间
   - "需要安装psutil库"：运行 `pip install psutil`

3. **网络工具错误**：
   - "无效的URL格式"：检查URL是否正确
   - "禁止访问本地网络地址"：网络工具禁止访问localhost等地址
   - "网络连接失败"：检查网络连接和防火墙设置

4. **数据处理工具错误**：
   - "JSON格式无效"：检查JSON语法是否正确
   - "正则表达式错误"：检查正则表达式语法
   - "数学表达式错误"：检查数学表达式格式

**通用解决方案：**
1. 检查参数格式是否正确
2. 查看详细的错误信息
3. 确保有足够的权限
4. 检查依赖是否安装完整

### Q: 如何查看工具使用统计？

**方法1：程序运行中查看**
```
Agent会自动显示工具使用统计：
📊 工具使用统计：file_read: 3次 (100.0%成功) 平均0.12秒; system_info: 1次 (100.0%成功) 平均0.05秒
```

**方法2：获取详细统计**
```python
# 在代码中获取详细统计
stats = agent.get_detailed_stats()
print(f"总工具调用次数: {stats['total_tool_calls']}")
print(f"剩余调用次数: {stats['remaining_calls']}")
```

**方法3：重置统计**
```python
agent.reset_statistics()
```

### Q: 如何控制工具权限？

**权限控制方法：**
```python
# 只允许特定的工具
agent = Agent(
    tools=all_tools,  # 所有工具
    allowed_tools=["file_read", "system_info", "http_request"],  # 只允许这些工具
    max_tool_usage=100  # 限制总使用次数
)
```

**使用场景：**
- 生产环境：限制危险工具的使用
- 测试环境：只启用必要的工具
- 用户权限：根据用户角色启用不同工具

## 🔧 错误处理改进（增强版）

### 已实施的改进（增强版）

1. **页面稳定等待**：在操作元素前等待页面加载完成
2. **改进错误信息**：提供具体的错误原因和建议
3. **区分错误类型**：超时、关闭、未找到等不同错误有不同的处理
4. **工具使用统计**：记录工具调用次数、成功率、执行时间
5. **权限控制系统**：支持工具级别的权限控制
6. **安全限制增强**：文件大小限制、命令过滤、网络访问限制
7. **资源自动清理**：自动清理工具占用的资源

### 使用建议（增强版）

**最佳实践：**
1. **操作前获取状态**：复杂操作前先使用 `get_state`
2. **分步执行**：将复杂任务分解为简单步骤
3. **错误恢复**：如果操作失败，先获取状态再重试
4. **权限控制**：根据使用场景限制工具权限
5. **资源管理**：及时调用 `cleanup()` 释放资源
6. **统计监控**：定期查看工具使用统计，优化使用策略
7. **安全第一**：始终遵循安全最佳实践，避免危险操作

**示例流程：**
```
用户: 打开百度，搜索"Python教程"，点击第一个结果

Agent执行流程：
1. go_to_url("https://www.baidu.com")
2. wait(2)  # 等待页面稳定
3. get_state()  # 获取页面元素列表
4. input_text(index=0, text="Python教程")  # 根据状态选择索引
5. click_element(index=1)  # 点击搜索按钮
6. wait(2)  # 等待搜索结果加载
7. get_state()  # 获取搜索结果页面状态
8. click_element(index=0)  # 点击第一个结果
```

## 📊 项目分析（增强版）

### 项目优势（增强版）

1. **代码质量高**：结构清晰，注释完整，类型安全
2. **功能丰富**：20+工具覆盖文件、系统、数据、网络等多个领域
3. **易于扩展**：工具系统设计良好，易于添加新工具
4. **错误处理完善**：关键操作都有异常捕获和自动恢复
5. **安全机制全面**：文件限制、命令过滤、网络访问控制等多重安全保护
6. **统计监控完善**：完整的工具使用统计和权限控制系统
7. **异步架构优秀**：完整的async/await支持，性能良好
8. **文档齐全**：包含详细的使用示例、分析报告和维护指南

### 当前状态（增强版）

1. **浏览器工具**：
   - ✅ 已改进错误处理（自动滚动重试）
   - ✅ 已添加页面稳定等待
   - ✅ 已集成到增强版系统
   - ⚠️ 可能出现滚动超时警告（但不影响最终结果）

2. **文件操作工具**：
   - ✅ 支持文件读取、写入、目录列表
   - ✅ 包含安全限制（文件大小、路径检查）
   - ✅ 自动编码处理

3. **系统操作工具**：
   - ✅ 支持命令执行、系统信息、Python代码执行
   - ✅ 包含危险命令过滤和安全沙箱
   - ✅ 超时控制和输出限制

4. **数据处理工具**：
   - ✅ 支持JSON处理、文本处理、数学计算
   - ✅ 包含数据验证和错误处理
   - ✅ 支持复杂的数据操作

5. **网络工具**：
   - ✅ 支持HTTP请求、网络测试、WebSocket
   - ✅ 包含网络访问限制和安全检查
   - ✅ 超时控制和SSL验证

6. **智能体增强**：
   - ✅ 工具使用统计和权限控制
   - ✅ 资源自动清理
   - ✅ 详细的错误报告

7. **任务规划**：简化版Think-Act循环，支持复杂任务分解

8. **错误恢复**：
   - ✅ 已实现自动重试机制
   - ✅ 已改进错误信息和分类
   - ✅ 已添加工具级别的错误统计

### 改进方向（已完成）

**已完成的改进：**
1. **工具扩展**：
   - ✅ 添加20+新工具（文件、系统、数据、网络）
   - ✅ 完善工具安全机制
   - ✅ 添加工具使用统计

2. **智能体增强**：
   - ✅ 添加权限控制系统
   - ✅ 添加工具使用限制
   - ✅ 完善资源管理

3. **错误处理**：
   - ✅ 改进错误分类和信息
   - ✅ 添加自动重试机制
   - ✅ 完善安全限制

4. **文档完善**：
   - ✅ 添加详细使用示例
   - ✅ 创建完整项目文档
   - ✅ 提供测试脚本

**未来改进方向：**
1. **性能优化**：
   - 工具调用并行化
   - 缓存机制优化
   - 内存使用优化

2. **功能增强**：
   - 添加更多工具类型
   - 支持插件系统
   - 添加Web界面

3. **用户体验**：
   - 添加进度显示
   - 支持流式输出
   - 改进交互界面

**已实现的用户体验改进：**
- ✅ 增强版主程序界面
- ✅ 详细的工具使用反馈
- ✅ 实时统计信息显示
- ✅ 完善的错误提示

**详细文档（增强版）：**
- `项目综合分析报告.md` - 完整的项目分析
- `新工具使用示例.md` - 新工具详细使用指南
- `项目健康度检查报告.md` - 项目状态评估
- `项目维护指南.md` - 维护和开发指南
- `技术架构图.md` - 架构设计说明
- `项目执行摘要.md` - 快速参考指南

## 🧪 测试与验证

### 1. 快速测试
```bash
# 检查依赖
python test_new_tools.py --check

# 快速测试
python test_new_tools.py --quick

# 完整测试
python test_new_tools.py --full
```

### 2. 运行增强版程序
```bash
# 运行增强版主程序
python main.py

# 示例交互
👤 你: 读取README.md文件
🤔 思考中...
🛠️  执行工具：file_read，参数：{'path': 'README.md'}
✅  工具 'file_read' 执行成功，耗时：0.02秒
🤖 助手: 文件内容：[显示文件内容]

👤 你: 查看系统信息
🤔 思考中...
🛠️  执行工具：system_info，参数：{'info_type': 'all'}
✅  工具 'system_info' 执行成功，耗时：0.05秒
🤖 助手: [显示系统信息]
```

### 3. 查看统计信息
程序运行时会自动显示工具使用统计，也可以在代码中获取详细统计：
```python
stats = agent.get_detailed_stats()
print(f"工具调用统计: {stats}")
```

## 📄 许可证

本项目参考OpenManus设计，仅供学习和研究使用。

## 🤝 贡献指南

### 1. 报告问题
- 使用GitHub Issues报告bug或提出功能建议
- 提供详细的复现步骤和环境信息

### 2. 提交代码
- 遵循现有的代码风格和结构
- 添加必要的测试用例
- 更新相关文档

### 3. 添加新工具
参考现有工具的实现方式：
1. 在 `tool/` 目录下创建新工具文件
2. 继承 `BaseTool` 基类
3. 实现必要的安全检查和错误处理
4. 在主程序中注册新工具
5. 添加使用示例和测试

### 4. 文档贡献
- 更新README.md
- 添加工具使用示例
- 完善API文档

## 🔗 相关资源

### 项目文档
- `README.md` - 项目主文档（本文档）
- `新工具使用示例.md` - 新工具详细使用指南
- `项目综合分析报告.md` - 完整项目分析
- `项目维护指南.md` - 维护和开发指南

### 测试工具
- `test_new_tools.py` - 新工具测试脚本
- 支持快速测试、完整测试和依赖检查

### 配置说明
- `config/config.toml` - 配置文件
- `requirements.txt` - 依赖列表

### 核心代码
- `main.py` - 增强版主程序
- `agent.py` - 增强版智能体
- `tool/` - 所有工具实现

---

**项目版本**: 2.0.0 (增强版)  
**最后更新**: 2024年  
**工具数量**: 20+  
**主要特性**: 多工具支持、权限控制、使用统计、安全机制  
**状态**: 稳定可用，持续改进中  

> 提示：建议先运行 `python test_new_tools.py --quick` 测试新工具是否正常工作，然后再运行主程序。

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**项目作者**: Fanghao
**基于**: OpenManus
**版本**: 1.0.0 (简化版)
**最后更新**: 2024年
