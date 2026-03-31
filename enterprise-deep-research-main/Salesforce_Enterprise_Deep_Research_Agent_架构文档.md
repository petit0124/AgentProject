# Salesforce Enterprise Deep Research Agent 架构文档

## 目录
1. [系统概述](#系统概述)
2. [Prompt 工程结构](#prompt-工程结构)
3. [Agent 架构](#agent-架构)
4. [工作流图实现](#工作流图实现)
5. [核心代码实现](#核心代码实现)

---

## 系统概述

Salesforce Enterprise Deep Research Agent 是一个基于 LangGraph 的多智能体研究系统，能够：
- 自动分解复杂研究主题
- 执行多轮深度研究
- 整合来自多个来源的信息
- 生成高质量的研究报告
- 支持数据库查询（Text2SQL）
- 支持用户引导（Steering）功能

---

## Prompt 工程结构

### 1. Prompt 文件组织

```
src/
├── prompts.py              # 主要研究模式的 prompts
├── prompts_qa.py           # QA 模式的 prompts
└── prompts_benchmark.py    # Benchmark 模式的 prompts
```

### 2. 核心 Prompt 模板

#### 2.1 查询分解 Prompt (`query_writer_instructions`)

**位置**: `src/prompts.py` (第4-405行)

**功能**: 将用户的研究主题分解为可执行的搜索查询

**结构**:
```python
query_writer_instructions = r"""
<TIME_CONTEXT>
Current date: {current_date}
Current year: {current_year}
One year ago: {one_year_ago}
</TIME_CONTEXT>

<AUGMENT_KNOWLEDGE_CONTEXT>
{AUGMENT_KNOWLEDGE_CONTEXT}
</AUGMENT_KNOWLEDGE_CONTEXT>

<DATABASE_CONTEXT>
{DATABASE_CONTEXT}
</DATABASE_CONTEXT>

[核心指令部分]
- 主题分析和策略
- 研究阶段指导
- 查询要求
- 格式指南
- 工具选择（search, math, code, data, text2sql）
"""
```

**关键特性**:
- 支持复杂主题分解为多个子主题
- 支持数据库查询（text2sql）和网络搜索的智能选择
- 支持用户上传知识的集成
- 时间敏感性处理（当前日期、年份等）

#### 2.2 摘要生成 Prompt (`summarizer_instructions`)

**位置**: `src/prompts.py` (第411-776行)

**功能**: 将搜索结果合成为综合研究报告

**结构**:
```python
summarizer_instructions = r"""
<TIME_CONTEXT>...</TIME_CONTEXT>
<AUGMENT_KNOWLEDGE_CONTEXT>...</AUGMENT_KNOWLEDGE_CONTEXT>

<GOAL>
生成全面的研究质量综合报告
</GOAL>

[核心指令]
- 反幻觉指令（ANTI_HALLUCINATION_DIRECTIVE）
- 主题聚焦指令（TOPIC_FOCUS_DIRECTIVE）
- 来源质量评估（SOURCE_QUALITY_ASSESSMENT）
- 技术内容指导（TECHNICAL_CONTENT_GUIDANCE）
- 矛盾处理协议（CONTRADICTION_HANDLING_PROTOCOL）
- 引用要求（CITATION_REQUIREMENTS）
"""
```

**关键特性**:
- 严格的引用要求（必须标注来源）
- 反幻觉机制（只使用来源中的信息）
- 多源信息整合策略
- 技术内容的深度处理

#### 2.3 反思 Prompt (`reflection_instructions`)

**位置**: `src/prompts.py` (第781-1390行)

**功能**: 评估研究报告的完整性，识别知识缺口

**结构**:
```python
reflection_instructions = r"""
<TIME_CONTEXT>...</TIME_CONTEXT>
<AUGMENT_KNOWLEDGE_CONTEXT>...</AUGMENT_KNOWLEDGE_CONTEXT>

<GOAL>
评估研究完整性，识别知识缺口
</GOAL>

<TODO_DRIVEN_REFLECTION>
- 待完成任务列表
- 已完成任务列表
- 用户引导消息
- 任务更新逻辑（标记完成、取消、添加新任务）
</TODO_DRIVEN_REFLECTION>

[评估维度]
- 主题分类
- 知识缺口识别
- 后续查询生成
- 研究完成度判断
"""
```

**关键特性**:
- 基于任务队列的反思机制
- 支持用户引导（Steering）消息处理
- 知识缺口识别和后续查询生成
- 研究完成度评估

#### 2.4 报告最终化 Prompt (`finalize_report_instructions`)

**位置**: `src/prompts.py` (第1391行开始)

**功能**: 生成最终的研究报告

**关键特性**:
- 报告格式化和优化
- 最终引用整理
- Markdown 格式输出

### 3. 模式特定的 Prompts

#### 3.1 QA 模式 (`prompts_qa.py`)

用于简单问答场景：
- `QUESTION_DECOMPOSITION_PROMPT`: 问题分解
- `ANSWER_GENERATION_PROMPT`: 答案生成
- `ANSWER_REFLECTION_PROMPT`: 答案反思
- `FINAL_ANSWER_PROMPT`: 最终答案

#### 3.2 Benchmark 模式 (`prompts_benchmark.py`)

用于基准测试场景，包含完整的引用处理。

---

## Agent 架构

### 1. 多智能体系统

系统采用模块化的多智能体架构：

```
MasterResearchAgent (主控智能体)
    ├── 负责：查询分解、研究规划、协调
    │
    ├── SearchAgent (搜索智能体)
    │   ├── general_search: 通用搜索
    │   ├── academic_search: 学术搜索
    │   ├── github_search: 代码搜索
    │   ├── linkedin_search: 专业搜索
    │   └── text2sql_search: 数据库查询
    │
    ├── VisualizationAgent (可视化智能体)
    │   └── 生成数据可视化
    │
    └── ResultCombiner (结果整合器)
        └── 整合多源结果
```

### 2. 核心 Agent 类

#### 2.1 MasterResearchAgent

**位置**: `src/agent_architecture.py` (第29-2027行)

**主要方法**:
```python
class MasterResearchAgent:
    async def decompose_topic(...)
        """分解研究主题为子任务"""
    
    async def plan_research(...)
        """制定研究计划"""
    
    async def execute_research(...)
        """执行研究任务"""
    
    async def plan_adaptive_research(...)
        """自适应研究规划"""
```

**职责**:
- 分析研究主题的复杂性
- 将复杂主题分解为子主题
- 协调各个专业智能体
- 管理研究循环

#### 2.2 SearchAgent

**位置**: `src/agent_architecture.py` (第2029-2269行)

**主要方法**:
```python
class SearchAgent:
    async def general_search(query)
        """执行通用搜索"""
    
    async def academic_search(query)
        """执行学术搜索"""
    
    async def github_search(query)
        """执行 GitHub 搜索"""
    
    async def text2sql_search(query, db_id)
        """执行数据库查询"""
    
    async def execute(subtask, tool_executor)
        """执行搜索子任务"""
```

**职责**:
- 根据子任务选择合适的搜索工具
- 执行具体的搜索操作
- 处理搜索结果

---

## 工作流图实现

### 1. 状态图结构

系统使用 LangGraph 构建状态机，主要节点包括：

```
START
  ↓
multi_agents_network (多智能体网络)
  ↓
  ├─→ [QA/Benchmark模式] → validate_context_sufficiency → generate_answer
  │                                                          ↓
  │                                                    reflect_answer
  │                                                          ↓
  │                                                    [继续研究/完成]
  │
  └─→ [常规模式] → generate_report (生成报告)
                      ↓
                 reflect_on_report (反思报告)
                      ↓
                 [继续研究/完成]
                      ↓
                 finalize_report (最终化报告)
                      ↓
                    END
```

### 2. 核心节点实现

#### 2.1 multi_agents_network 节点

**位置**: `src/graph.py` (第284行开始)

**功能**: 多智能体网络入口点

```python
async def async_multi_agents_network(state: SummaryState, callbacks=None):
    """
    异步执行研究的多智能体网络
    
    流程:
    1. 创建 MasterResearchAgent
    2. 执行研究计划
    3. 更新状态
    """
    master_agent = MasterResearchAgent(config)
    await master_agent.execute_research(state, callbacks, database_info)
    return state
```

#### 2.2 generate_report 节点

**功能**: 生成研究报告

**流程**:
1. 使用 `summarizer_instructions` prompt
2. 整合所有搜索结果
3. 生成 Markdown 格式报告
4. 添加引用

#### 2.3 reflect_on_report 节点

**功能**: 反思报告完整性

**流程**:
1. 使用 `reflection_instructions` prompt
2. 评估报告完整性
3. 识别知识缺口
4. 更新任务队列
5. 决定是否继续研究

#### 2.4 finalize_report 节点

**功能**: 最终化报告

**流程**:
1. 使用 `finalize_report_instructions` prompt
2. 优化报告格式
3. 整理最终引用
4. 生成最终输出

### 3. 路由函数

#### 3.1 route_research

**位置**: `src/graph.py` (第3138行)

**功能**: 决定研究是否继续

```python
def route_research(state: SummaryState, config: RunnableConfig):
    """
    路由决策逻辑:
    - 检查是否达到最大循环数
    - 检查 research_complete 标志
    - 检查是否有后续查询
    """
    if state.research_loop_count >= max_loops:
        return "finalize_report"
    
    if state.research_complete:
        return "finalize_report"
    
    if state.research_loop_count == 1:
        return "multi_agents_network"  # 强制第一轮继续
    
    if not state.search_query:
        return "finalize_report"
    
    return "multi_agents_network"  # 继续研究
```

#### 3.2 route_after_multi_agents_decision

**位置**: `src/graph.py` (第5218行)

**功能**: 多智能体网络后的路由决策

```python
def route_after_multi_agents_decision(state):
    """根据模式决定下一步"""
    if state.qa_mode or state.benchmark_mode:
        return "validate_context_sufficiency"
    else:
        return "generate_report"
```

### 4. 图构建代码

**位置**: `src/graph.py` (第5189-5276行)

```python
def create_graph():
    """创建 LangGraph 状态图"""
    builder = StateGraph(
        SummaryState,
        input=SummaryStateInput,
        output=SummaryStateOutput,
        config_schema=Configuration,
    )
    
    # 添加节点
    builder.add_node("multi_agents_network", async_multi_agents_network)
    builder.add_node("generate_report", generate_report)
    builder.add_node("reflect_on_report", reflect_on_report)
    builder.add_node("finalize_report", finalize_report)
    builder.add_node("generate_answer", generate_answer)
    builder.add_node("reflect_answer", reflect_answer)
    builder.add_node("finalize_answer", finalize_answer)
    builder.add_node("validate_context_sufficiency", validate_context_sufficiency)
    builder.add_node("refine_query", refine_query)
    
    # 添加边和条件路由
    builder.add_edge(START, "multi_agents_network")
    builder.add_conditional_edges(
        "multi_agents_network",
        route_after_multi_agents_decision,
        {
            "validate_context_sufficiency": "validate_context_sufficiency",
            "generate_report": "generate_report",
        },
    )
    # ... 更多路由逻辑
    
    return builder.compile()
```

---

## 核心代码实现

### 1. 状态管理

#### SummaryState 类

**位置**: `src/state.py` (第22-456行)

```python
class SummaryState(BaseModel):
    """研究状态数据模型"""
    research_topic: str
    search_query: str = ""
    running_summary: str = ""
    research_complete: bool = False
    knowledge_gap: str = ""
    research_loop_count: int = 0
    sources_gathered: List[str] = []
    web_research_results: List[Dict[str, Any]] = []
    subtopic_queries: List[str] = []
    research_plan: Optional[Dict[str, Any]] = None
    database_info: Optional[List[Dict[str, Any]]] = None
    steering_todo: Optional[Any] = None
    # ... 更多字段
```

### 2. 工具系统

#### 2.1 Text2SQL 工具

**位置**: `src/tools/text2sql_tool.py`

```python
class Text2SQLTool:
    """将自然语言查询转换为 SQL 并执行"""
    
    def upload_database(self, file_content, filename, file_type):
        """上传数据库文件"""
        # 处理 SQLite/CSV/JSON 文件
        # 提取模式信息
        # 返回数据库 ID
    
    def query_database(self, db_id, natural_language_query):
        """查询数据库"""
        # 1. 使用 LLM 将自然语言转换为 SQL
        # 2. 执行 SQL 查询
        # 3. 返回结果
```

#### 2.2 搜索工具注册表

**位置**: `src/tools/registry.py`

```python
class ToolRegistry:
    """工具注册表"""
    
    def __init__(self, config):
        self.tools = {}
        self._register_search_tools()
        self._register_mcp_tools()
    
    def get_tool(self, tool_name):
        """获取工具实例"""
        return self.tools.get(tool_name)
```

### 3. 主要执行流程

#### 3.1 研究执行流程

```python
# 1. 初始化状态
state = SummaryState(
    research_topic="研究主题",
    extra_effort=False,
    minimum_effort=False,
)

# 2. 创建图实例
graph = create_graph()

# 3. 执行研究
result = await graph.ainvoke(
    state,
    config={"configurable": {...}}
)

# 4. 获取结果
final_report = result["markdown_report"]
sources = result["sources_gathered"]
```

#### 3.2 查询分解流程

```python
# 在 MasterResearchAgent.decompose_topic 中
async def decompose_topic(self, query, knowledge_gap, ...):
    # 1. 准备 Prompt
    prompt = query_writer_instructions.format(
        current_date=CURRENT_DATE,
        current_year=CURRENT_YEAR,
        research_topic=query,
        # ... 更多参数
    )
    
    # 2. 调用 LLM
    llm_client = get_async_llm_client(provider, model)
    response = await llm_client.ainvoke(prompt)
    
    # 3. 解析 JSON 响应
    decomposition = json.loads(response)
    
    # 4. 返回分解结果
    return {
        "topic_complexity": decomposition["topic_complexity"],
        "subtopics": decomposition["subtopics"],
        # ...
    }
```

#### 3.3 报告生成流程

```python
# 在 generate_report 节点中
async def generate_report(state: SummaryState):
    # 1. 准备摘要 Prompt
    prompt = summarizer_instructions.format(
        research_topic=state.research_topic,
        search_results=state.web_research_results,
        # ...
    )
    
    # 2. 调用 LLM 生成报告
    llm_client = get_llm_client(provider, model)
    report = await llm_client.ainvoke(prompt)
    
    # 3. 后处理（添加引用、格式化）
    final_report = post_process_report(report, state.source_citations)
    
    # 4. 更新状态
    return {
        "running_summary": final_report,
        "markdown_report": final_report,
    }
```

### 4. 数据库集成

```python
# 数据库信息传递
database_info = [
    {
        "id": "db_123",
        "filename": "sales_data.db",
        "file_type": "sqlite",
        "tables": ["customers", "orders", "products"],
    }
]

# 在 MasterAgent 中访问
if hasattr(self, "database_info") and self.database_info:
    database_context = f"""
    DATABASE AVAILABLE:
    - {db['filename']} with tables: {', '.join(db['tables'])}
    
    TOOL SELECTION:
    - Questions about uploaded data → use "text2sql"
    - Questions about external info → use search tools
    """
```

### 5. Steering 系统

```python
# 在 SummaryState 中
class SummaryState:
    steering_enabled: bool = False
    steering_todo: Optional[ResearchTodoManager] = None
    
    async def add_steering_message(self, message: str):
        """添加用户引导消息"""
        await self.steering_todo.add_user_message(message)
    
    def get_steering_plan(self) -> str:
        """获取当前引导计划（todo.md 格式）"""
        return self.steering_todo.get_todo_md()
```

---

## 调用流程图

### 完整研究流程

```
用户输入研究主题
    ↓
创建 SummaryState
    ↓
初始化 LangGraph
    ↓
┌─────────────────────────────────────┐
│ multi_agents_network                │
│  ├─ MasterAgent.decompose_topic     │
│  │   └─ 使用 query_writer_instructions │
│  │                                    │
│  ├─ MasterAgent.execute_research    │
│  │   ├─ 创建研究计划                  │
│  │   ├─ 并行执行子任务                │
│  │   │   ├─ SearchAgent.general_search │
│  │   │   ├─ SearchAgent.academic_search │
│  │   │   ├─ SearchAgent.text2sql_search │
│  │   │   └─ ...                      │
│  │   └─ 收集结果                      │
│  └─ 更新 state.web_research_results │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ generate_report                      │
│  └─ 使用 summarizer_instructions    │
│     └─ 生成 running_summary          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ reflect_on_report                   │
│  └─ 使用 reflection_instructions   │
│     ├─ 评估完整性                    │
│     ├─ 识别知识缺口                  │
│     ├─ 更新任务队列                  │
│     └─ 决定是否继续                  │
└─────────────────────────────────────┘
    ↓
    ├─ [继续研究] → multi_agents_network
    │
    └─ [完成] → finalize_report
                  ↓
                END
```

### Prompt 调用链

```
1. query_writer_instructions
   └─ 在 MasterAgent.decompose_topic 中使用
      └─ 输入: 研究主题、知识缺口、数据库信息
      └─ 输出: JSON 格式的查询分解结果

2. summarizer_instructions
   └─ 在 generate_report 节点中使用
      └─ 输入: 搜索结果、当前摘要、研究主题
      └─ 输出: 综合研究报告

3. reflection_instructions
   └─ 在 reflect_on_report 节点中使用
      └─ 输入: 当前报告、任务队列、用户引导
      └─ 输出: 知识缺口、后续查询、完成度判断

4. finalize_report_instructions
   └─ 在 finalize_report 节点中使用
      └─ 输入: 运行摘要、所有来源
      └─ 输出: 最终格式化的报告
```

---

## 关键技术特性

### 1. 多模式支持
- **常规模式**: 生成完整研究报告
- **QA 模式**: 简单问答（1轮研究）
- **Benchmark 模式**: 基准测试模式（完整引用处理）

### 2. 工具集成
- **搜索工具**: general_search, academic_search, github_search, linkedin_search
- **数据库工具**: text2sql（支持 SQLite, CSV, JSON）
- **MCP 工具**: 通过 MCP 协议集成外部工具

### 3. 用户引导（Steering）
- 支持实时用户反馈
- 基于任务队列的管理
- Todo.md 格式的计划跟踪

### 4. 知识增强
- 支持用户上传外部知识文档
- 自动识别知识缺口
- 智能补充和验证

---

## 总结

Salesforce Enterprise Deep Research Agent 是一个功能强大的多智能体研究系统，通过精心设计的 Prompt 工程、模块化的 Agent 架构和灵活的状态图工作流，实现了高质量的研究报告生成。系统支持多种研究模式、工具集成和用户交互，能够适应不同的研究场景和需求。


