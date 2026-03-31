# QA 模式和 Benchmark 模式说明

## 📋 概述

Salesforce Enterprise Deep Research Agent 支持三种运行模式：

1. **常规模式** (默认): 生成完整的研究报告
2. **QA 模式** (`qa_mode=True`): 快速问答模式
3. **Benchmark 模式** (`benchmark_mode=True`): 基准测试模式

---

## 🔍 QA 模式 (Question-Answering Mode)

### 用途
**快速回答简单问题**，不需要生成完整的研究报告。

### 特点

1. **单轮研究** (1 loop)
   - 只执行一次搜索和研究循环
   - 快速响应，适合简单问题

2. **简洁答案**
   - 生成直接、简洁的答案
   - 不包含完整的引用处理
   - 适合快速获取信息

3. **工作流程**
   ```
   用户问题 → 搜索 → 生成答案 → 结束
   ```

### 使用场景

- ✅ 简单的事实性问题
- ✅ 快速查询
- ✅ 不需要详细报告的场景
- ✅ 资源受限的环境

### 代码示例

```python
from src.graph import create_graph
from src.state import SummaryState

# 创建 QA 模式状态
state = SummaryState(
    research_topic="Who is the current CEO of Microsoft?",
    qa_mode=True,  # 启用 QA 模式
    minimum_effort=False,  # QA 模式会自动设置为 1 轮
)

# 执行研究
graph = create_graph()
result = await graph.ainvoke(state)
```

### 命令行使用

```bash
python benchmarks/run_research.py "Who is the current CEO of Microsoft?" --qa-mode
```

### 输出格式

```json
{
    "answer": "Satya Nadella is the current CEO of Microsoft.",
    "confidence_level": "HIGH",
    "sources": ["source1", "source2"],
    "research_loop_count": 1
}
```

---

## 🎯 Benchmark 模式 (Benchmark Testing Mode)

### 用途
**用于评估和测试系统性能**，生成结构化答案并支持与预期答案对比。

### 特点

1. **多轮研究**
   - 可以执行多轮研究循环（默认 3-5 轮）
   - 更深入的研究和分析

2. **完整引用处理**
   - 详细的引用和来源标注
   - 支持答案验证（与预期答案对比）
   - 适合学术和评估场景

3. **结构化输出**
   - 包含答案、置信度、推理过程
   - 支持答案验证和评分
   - 完整的执行轨迹记录

4. **工作流程**
   ```
   用户问题 → 搜索 → 生成答案 → 反思答案 → 
   [继续研究/完成] → 最终化答案 → 验证答案（可选）
   ```

### 使用场景

- ✅ 基准测试和评估
- ✅ 学术研究
- ✅ 系统性能测试
- ✅ 需要详细引用和验证的场景
- ✅ DeepResearchBench、DeepConsult 等评估框架

### 代码示例

```python
from src.graph import create_graph
from src.state import SummaryState

# 创建 Benchmark 模式状态
state = SummaryState(
    research_topic="What are the latest developments in quantum computing?",
    benchmark_mode=True,  # 启用 Benchmark 模式
    extra_effort=False,
    minimum_effort=False,
)

# 执行研究
graph = create_graph()
result = await graph.ainvoke(state)

# 获取基准测试结果
benchmark_result = result.get("benchmark_result")
if benchmark_result:
    print(f"Answer: {benchmark_result['answer']}")
    print(f"Confidence: {benchmark_result['confidence_level']}")
    print(f"Sources: {benchmark_result['sources']}")
```

### 命令行使用

```bash
python benchmarks/run_research.py \
    "What are the latest developments in quantum computing?" \
    --benchmark-mode \
    --max-loops 5 \
    --provider google \
    --model gemini-2.5-pro
```

### 输出格式

```json
{
    "benchmark_result": {
        "answer": "详细的答案内容...",
        "confidence_level": "HIGH",
        "reasoning": "推理过程...",
        "supporting_evidence": ["证据1", "证据2"],
        "sources": [
            {
                "url": "https://example.com",
                "title": "Source Title",
                "citation_number": 1
            }
        ],
        "verification_score": 0.95  // 如果提供了预期答案
    },
    "research_loop_count": 3,
    "execution_trace": [...],  // 完整的执行轨迹
    "previous_answers": [...],  // 所有轮次的答案历史
    "reflection_history": [...]  // 反思历史
}
```

---

## 🔄 三种模式对比

| 特性 | 常规模式 | QA 模式 | Benchmark 模式 |
|------|---------|---------|---------------|
| **研究轮数** | 3-5 轮（可配置） | 1 轮（固定） | 3-5 轮（可配置） |
| **输出格式** | 完整研究报告 | 简洁答案 | 结构化答案 |
| **引用处理** | 完整引用 | 简化引用 | 完整引用+验证 |
| **执行时间** | 较长 | 最短 | 较长 |
| **适用场景** | 深度研究 | 快速问答 | 评估测试 |
| **答案验证** | ❌ | ❌ | ✅ |
| **执行轨迹** | 基础 | 基础 | 完整 |
| **答案历史** | ❌ | ❌ | ✅ |

---

## 📊 工作流对比

### 常规模式工作流

```
START
  ↓
multi_agents_network (多轮研究)
  ↓
generate_report (生成报告)
  ↓
reflect_on_report (反思报告)
  ↓
[继续研究/完成]
  ↓
finalize_report (最终化报告)
  ↓
END
```

### QA 模式工作流

```
START
  ↓
multi_agents_network (1轮研究)
  ↓
validate_context_sufficiency
  ↓
generate_answer (生成答案)
  ↓
reflect_answer (反思答案)
  ↓
finalize_answer (最终化答案)
  ↓
END
```

### Benchmark 模式工作流

```
START
  ↓
multi_agents_network (多轮研究)
  ↓
validate_context_sufficiency
  ↓
generate_answer (生成答案)
  ↓
reflect_answer (反思答案)
  ↓
[继续研究/完成]
  ↓
finalize_answer (最终化答案)
  ↓
[可选] verify_answer (验证答案)
  ↓
END
```

---

## 🛠️ 技术实现细节

### Prompt 差异

#### QA 模式使用的 Prompts (`prompts_qa.py`)
- `QA_QUESTION_DECOMPOSITION_PROMPT`: 问题分解
- `QA_ANSWER_GENERATION_PROMPT`: 答案生成
- `QA_ANSWER_REFLECTION_PROMPT`: 答案反思
- `QA_FINAL_ANSWER_PROMPT`: 最终答案

#### Benchmark 模式使用的 Prompts (`prompts_benchmark.py`)
- `BENCHMARK_QUESTION_DECOMPOSITION_PROMPT`: 问题分解（更详细）
- `BENCHMARK_ANSWER_GENERATION_PROMPT`: 答案生成（包含完整引用）
- `BENCHMARK_ANSWER_REFLECTION_PROMPT`: 答案反思（更严格）
- `BENCHMARK_FINAL_ANSWER_PROMPT`: 最终答案（结构化）
- `BENCHMARK_ANSWER_VERIFICATION_PROMPT`: 答案验证（可选）

### 路由逻辑差异

```python
# 在 graph.py 中
def route_after_multi_agents_decision(state):
    """多智能体网络后的路由决策"""
    if state.qa_mode or state.benchmark_mode:
        return "validate_context_sufficiency"  # QA/Benchmark 路径
    else:
        return "generate_report"  # 常规模式路径
```

### 研究循环数控制

```python
# 在 graph.py 中
def get_max_loops(configurable, extra_effort, minimum_effort, benchmark_mode, qa_mode):
    """获取最大研究循环数"""
    # QA 模式强制为 1 轮
    if qa_mode:
        return 1
    
    # Benchmark 模式使用配置的循环数
    if benchmark_mode:
        return configurable.max_web_research_loops  # 默认 3-5
    
    # 常规模式
    return configurable.max_web_research_loops
```

---

## 📝 使用建议

### 何时使用 QA 模式？

- ✅ 简单的事实性问题
- ✅ 需要快速响应的场景
- ✅ 资源受限的环境
- ✅ 不需要详细报告的场景

**示例问题**:
- "Who is the current CEO of Microsoft?"
- "What is the capital of France?"
- "When was Python created?"

### 何时使用 Benchmark 模式？

- ✅ 系统性能评估
- ✅ 学术研究
- ✅ 基准测试（DeepResearchBench、DeepConsult）
- ✅ 需要详细引用和验证的场景
- ✅ 复杂问题的深入分析

**示例问题**:
- "What are the latest developments in quantum computing?"
- "Analyze the impact of AI on healthcare"
- "Compare different approaches to climate change mitigation"

### 何时使用常规模式？

- ✅ 需要完整研究报告的场景
- ✅ 市场分析、竞品分析
- ✅ 深度技术研究
- ✅ 政策分析、法律研究

**示例问题**:
- "Comprehensive analysis of Salesforce AI products"
- "Market research on cloud computing trends"
- "Technical deep dive into agentic RAG systems"

---

## 🔧 配置示例

### QA 模式配置

```python
state = SummaryState(
    research_topic="简单问题",
    qa_mode=True,
    llm_provider="openai",
    llm_model="gpt-4",
    config={"max_web_research_loops": 1},  # QA 模式会覆盖为 1
)
```

### Benchmark 模式配置

```python
state = SummaryState(
    research_topic="复杂问题",
    benchmark_mode=True,
    extra_effort=False,
    llm_provider="google",
    llm_model="gemini-2.5-pro",
    config={"max_web_research_loops": 5},
)
```

### 常规模式配置

```python
state = SummaryState(
    research_topic="研究主题",
    qa_mode=False,
    benchmark_mode=False,
    extra_effort=True,
    llm_provider="openai",
    llm_model="gpt-4",
    config={"max_web_research_loops": 3},
)
```

---

## 📚 相关文件

- **QA 模式 Prompts**: `src/prompts_qa.py`
- **Benchmark 模式 Prompts**: `src/prompts_benchmark.py`
- **常规模式 Prompts**: `src/prompts.py`
- **图节点实现**: `src/graph.py`
- **基准测试脚本**: `benchmarks/run_research.py`
- **基准测试文档**: `benchmarks/README.md`

---

## 🎓 总结

- **QA 模式**: 快速、简洁，适合简单问题
- **Benchmark 模式**: 详细、结构化，适合评估和测试
- **常规模式**: 完整、深入，适合深度研究

选择合适的模式可以优化系统性能和资源使用，同时满足不同的使用场景需求。




