"""
Writer Agent
负责生成最终研究报告
"""
from langchain_core.prompts import ChatPromptTemplate
from src.config.llm_config import get_llm
from src.graph.state import ResearchState


class WriterAgent:
    """Writer Agent负责生成结构化报告"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.5)
        
        # 定义Writer的提示模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的研究报告撰写专家，擅长将复杂信息整理成结构清晰的报告。

你的任务是：
1. 整合所有研究分析内容
2. 生成结构化的Markdown格式报告
3. 确保逻辑连贯、层次清晰
4. 包含完整的参考来源

报告结构要求：
# [报告标题]

## 📋 执行摘要
[简明扼要的核心发现和结论]

## 🔍 研究背景
[说明研究的目的和范围]

## 📊 详细分析
[多个小节，每个小节覆盖一个关键主题]

### 主题1
[内容]

### 主题2
[内容]

## 💡 核心发现
[关键洞察和重要发现]

## 🎯 结论
[综合结论和建议]

## 📚 参考来源
[所有引用来源的列表，包含标题和链接]

格式要求：
- 使用Markdown语法
- 使用emoji增强可读性
- 段落之间适当留白
- 中文表述
- 专业且易读"""),
            ("user", """原始查询: {query}

研究计划:
{research_plan}

分析内容:
{analysis}

搜索来源:
{sources}

请生成完整的研究报告。""")
        ])
    
    def write_report(self, state: ResearchState) -> ResearchState:
        """
        生成最终报告
        
        Args:
            state: 当前状态
        
        Returns:
            更新后的状态
        """
        query = state["query"]
        research_plan = state.get("research_plan", [])
        analysis = state.get("analysis", [])
        search_results = state.get("search_results", [])
        
        # 格式化研究计划
        plan_text = "\n".join([f"- {topic}" for topic in research_plan])
        
        # 格式化分析内容
        analysis_text = "\n\n".join(analysis)
        
        # 格式化来源
        sources_text = ""
        for i, result in enumerate(search_results, 1):
            sources_text += f"{i}. [{result['title']}]({result['url']})\n"
        
        # 调用LLM生成报告
        chain = self.prompt | self.llm
        response = chain.invoke({
            "query": query,
            "research_plan": plan_text,
            "analysis": analysis_text,
            "sources": sources_text
        })
        
        report = response.content
        
        # 更新状态
        state["final_report"] = report
        state["current_step"] = "报告生成完成"
        state["messages"] = [f"📝 Writer Agent: 已生成完整研究报告，共 {len(report)} 字"]
        
        return state


# 创建Writer Agent实例
writer_agent = WriterAgent()
