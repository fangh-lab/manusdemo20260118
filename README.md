# FanghaoManus Demo - 简化版智能体项目

基于 OpenManus 设计的简化版智能体系统，专注于核心功能：**记忆管理**和**工具调用**。

## 📋 项目概述

这是一个最小化的智能体实现，包含：

- ✅ **记忆模块（Memory）**：管理对话历史
- ✅ **工具系统（Tools）**：浏览器操作工具
- ✅ **智能体（Agent）**：集成LLM和工具调用
- ✅ **配置系统**：支持多种LLM API

## 🏗️ 项目结构

```
fanghaomanusdemo/
├── config.py              # 配置加载模块
├── memory.py              # 记忆模块
├── llm.py                 # LLM封装模块
├── agent.py               # 智能体模块
├── main.py                # 主入口文件
├── tool/                  # 工具目录
│   ├── __init__.py
│   ├── base.py            # 工具基类
│   └── browser.py         # 浏览器工具
└── config/                # 配置文件目录
    └── config.toml        # 配置文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pydantic openai browser-use tomli
```

主要依赖：
- `pydantic`: 数据验证
- `openai`: OpenAI API客户端
- `browser-use`: 浏览器自动化
- `tomli`: TOML配置文件解析

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
python main.py
```

### 4. 使用示例

```
你: 帮我打开百度首页

助手: 正在打开百度首页...
```

## 📚 核心模块详解

### 1. 记忆模块（Memory）

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

### 2. 工具系统（Tools）

#### 2.1 工具基类（BaseTool）

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

#### 2.2 浏览器工具（BrowserTool）

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

### 3. 智能体（Agent）

**位置**: `agent.py`

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

### 4. LLM封装

**位置**: `llm.py`

**支持的API类型**：

- `openai`: OpenAI API（包括兼容的API如Ollama）
- `azure`: Azure OpenAI
- `anthropic`: Anthropic Claude API
- `ollama`: 本地Ollama

**核心方法**：

- `ask(messages)`: 普通对话（不使用工具）
- `ask_tool(messages, tools)`: 带工具调用的对话

### 5. 配置系统

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

### 完整流程示例

```
1. 用户输入: "打开百度，搜索'Python教程'"

2. Agent.run() 添加用户消息到Memory

3. _think() 调用LLM:
   - 传入: 对话历史 + 工具定义
   - LLM分析: 需要使用浏览器工具
   - LLM返回:
     {
       "tool_calls": [{
         "id": "call_123",
         "function": {
           "name": "browser",
           "arguments": '{"action": "go_to_url", "url": "https://www.baidu.com"}'
         }
       }]
     }

4. _act() 执行工具:
   - 解析 tool_calls
   - 调用 browser.execute(action="go_to_url", url="...")
   - 工具返回: ToolResult(output="已导航到: https://www.baidu.com")
   - 添加到Memory作为tool消息

5. 继续循环:
   - LLM看到工具执行结果
   - 决定下一步操作（例如：点击搜索框、输入文本等）
   - 继续执行工具...

6. 最终LLM返回文本回复，循环结束
```

### 工具调用的关键点

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

| 特性 | OpenManus | FanghaoManus Demo |
|------|-----------|-------------------|
| **规划功能** | ✅ 完整的PlanningFlow | ❌ 无（后续可加） |
| **工具数量** | 20+ 工具 | 1个（浏览器） |
| **记忆功能** | 完整的Memory系统 | ✅ 简化版Memory |
| **配置系统** | 复杂，支持多环境 | ✅ 简化版配置 |
| **代码复杂度** | 高（多层抽象） | 低（直接易懂） |

## 🔧 扩展开发

### 添加新工具

1. **创建工具类**（继承BaseTool）：

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
        # 实现工具逻辑
        return ToolResult(output="执行结果")
```

2. **注册到Agent**：

```python
from tool.my_tool import MyTool

agent = Agent(tools=[browser_tool, MyTool()])
```

### 修改记忆策略

编辑 `memory.py` 中的 `Memory.add_message()` 方法，可以自定义消息管理策略。

## 📝 注意事项

1. **API密钥安全**：不要将包含真实API密钥的配置文件提交到版本控制
2. **浏览器资源**：使用完浏览器工具后记得调用 `cleanup()` 释放资源
3. **消息限制**：注意控制消息数量，避免API费用过高
4. **错误处理**：工具执行失败时，错误信息会返回给LLM，LLM可以决定如何处理

## 🐛 常见问题与错误分析

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
```
# ✅ 正确方式：分步执行，每步等待
你: 打开百度搜索Python
→ Agent: go_to_url (打开百度)
→ Agent: wait(2) (等待页面稳定)
→ Agent: get_state (获取页面状态，查看元素列表)
→ Agent: input_text (根据状态选择正确的索引)
→ Agent: wait(1) (等待输入完成)
→ Agent: click_element (点击搜索按钮)
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

## 🔧 错误处理改进

### 已实施的改进

1. **页面稳定等待**：在操作元素前等待页面加载完成
2. **改进错误信息**：提供具体的错误原因和建议
3. **区分错误类型**：超时、关闭、未找到等不同错误有不同的处理

### 使用建议

**最佳实践：**
1. **操作前获取状态**：复杂操作前先使用 `get_state`
2. **分步执行**：将复杂任务分解为简单步骤
3. **错误恢复**：如果操作失败，先获取状态再重试

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

## 📊 项目分析

### 项目优势

1. **代码质量高**：结构清晰，注释完整
2. **易于理解**：简化设计，去除复杂模块
3. **易于扩展**：工具系统设计良好
4. **错误处理完善**：关键操作都有异常捕获
5. **自动恢复机制**：包含自动重试和错误恢复

### 当前状态

1. **浏览器工具**：
   - ✅ 已改进错误处理（自动滚动重试）
   - ✅ 已添加页面稳定等待
   - ⚠️ 可能出现滚动超时警告（但不影响最终结果）
   - ⏳ 计划添加自动状态检查

2. **任务规划**：没有复杂的任务规划能力（简化版设计）

3. **错误恢复**：
   - ✅ 已实现自动滚动重试
   - ✅ 已改进错误信息
   - ⏳ 计划实现更智能的错误恢复

### 改进方向

**短期（高优先级）：**
- ✅ 改进浏览器工具的错误处理（已实施）
- ✅ 添加自动滚动重试（已实施）
- ⏳ 添加页面状态自动检查
- ⏳ 实现智能错误恢复

**中期（中优先级）：**
- 添加任务完成判断
- 改进消息管理策略
- 添加日志系统

**长期（低优先级）：**
- 添加更多工具（文件、Python执行等）
- 性能优化
- 用户体验改进

**详细文档：**
- `项目分析报告.md` - 完整的项目分析
- `错误处理说明.md` - 错误处理详细说明
- `改进建议.md` - 详细的改进方案

## 📄 许可证

本项目参考OpenManus设计，仅供学习和研究使用。

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**项目作者**: Fanghao
**基于**: OpenManus
**版本**: 1.0.0 (简化版)
**最后更新**: 2024年
