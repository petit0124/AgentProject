"""
Supervisor Agent
负责任务分派和协调各个Agent
"""
from langchain_core.prompts import ChatPromptTemplate
from src.config.llm_config import get_llm
from src.graph.state import ResearchState


class SupervisorAgent:
    """Supervisor Agent负责制定研究计划"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.7)
        
        # 定义Supervisor的提示模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个研究协调专家，负责制定深度研究计划。

你的任务是：
1. 分析用户的研究查询
2. 将复杂问题分解为3-5个关键研究主题
3. 每个主题应该独立且具体，便于网络搜索

输出格式：
请以JSON格式返回研究主题列表，例如：
["主题1", "主题2", "主题3"]

注意：
- 主题应该具体且可搜索
- 覆盖问题的不同方面
- 使用中文表述"""),
            ("user", "用户查询: {query}\n\n请制定研究计划。")
        ])
    
    def create_plan(self, state: ResearchState) -> ResearchState:
        """
        制定研究计划
        
        Args:
            state: 当前状态
        
        Returns:
            更新后的状态
        """
        query = state["query"]
        
        # 调用LLM生成研究计划
        chain = self.prompt | self.llm
        response = chain.invoke({"query": query})
        
        # 解析响应
        import json
        import re
        
        # 尝试提取JSON
        content = response.content
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        
        if json_match:
            try:
                research_topics = json.loads(json_match.group())
            except:
                # 如果解析失败，使用默认分解
                research_topics = [
                    f"{query} - 核心概念",
                    f"{query} - 最新发展",
                    f"{query} - 应用案例"
                ]
        else:
            research_topics = [
                f"{query} - 核心概念",
                f"{query} - 最新发展",
                f"{query} - 应用案例"
            ]
        
        # 更新状态
        state["research_plan"] = research_topics
        state["current_step"] = "研究计划制定完成"
        state["messages"] = [f"📋 Supervisor: 已制定研究计划，包含 {len(research_topics)} 个主题"]
        
        return state


# 创建Supervisor实例
supervisor_agent = SupervisorAgent()
