"""
Research Agent
负责深度分析和思考
"""
from langchain_core.prompts import ChatPromptTemplate
from src.config.llm_config import get_llm
from src.graph.state import ResearchState
import json
import re


class ResearchAgent:
    """Research Agent负责深度分析搜索结果"""
    
    def __init__(self):
        self.llm = get_llm(temperature=0.7)
        
        # 定义Research的提示模板
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个深度研究分析专家，擅长从海量信息中提炼关键洞察。

你的任务是：
1. 仔细阅读所有搜索结果
2. 提取关键信息、数据和观点
3. 进行逻辑推理和综合分析
4. 发现不同来源之间的联系和矛盾
5. 形成结构化的分析结论

分析要求：
- 深入且全面
- 逻辑清晰
- 基于证据
- 使用中文
- 保持客观

输出格式：
以段落形式输出你的分析，包括：
- 核心发现
- 重要趋势
- 关键数据
- 专家观点
- 你的综合判断"""),
            ("user", """原始查询: {query}

当前迭代: 第 {iteration} 轮

已有分析内容:
{previous_analysis}

新的搜索结果:
{search_results}

请进行深度分析。""")
        ])
        
        # 定义评估提示模板
        self.evaluation_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个研究质量评估专家。

你的任务是评估当前研究的完整性，判断是否需要更多信息。

评估标准：
1. 信息是否充分回答了原始查询？
2. 是否存在明显的信息缺口？
3. 是否需要更深入的细节或案例？
4. 是否存在未解答的关键问题？

输出格式（JSON）：
{
  "need_more_research": true/false,
  "reason": "评估理由",
  "additional_questions": ["问题1", "问题2", "问题3"]
}

如果不需要更多研究，additional_questions可以为空数组。
如果需要更多研究，请提出2-3个具体的补充问题。"""),
            ("user", """原始查询: {query}

当前迭代: 第 {iteration} 轮 / 最大 {max_iterations} 轮

已完成的分析:
{analysis}

搜索来源数量: {source_count}

请评估是否需要进一步研究。""")
        ])
    
    def analyze(self, state: ResearchState) -> ResearchState:
        """
        分析搜索结果并评估是否需要更多研究
        
        Args:
            state: 当前状态
        
        Returns:
            更新后的状态
        """
        query = state["query"]
        search_results = state.get("search_results", [])
        iteration = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 1)
        previous_analysis = state.get("analysis", [])
        
        # 格式化搜索结果
        formatted_results = ""
        for i, result in enumerate(search_results, 1):
            formatted_results += f"\n【来源 {i}】\n"
            formatted_results += f"主题: {result.get('search_topic', 'N/A')}\n"
            formatted_results += f"标题: {result['title']}\n"
            formatted_results += f"链接: {result['url']}\n"
            formatted_results += f"内容: {result['content']}\n"
        
        # 格式化之前的分析
        previous_analysis_text = "\n\n---\n\n".join(previous_analysis) if previous_analysis else "无"
        
        # 调用LLM进行分析
        chain = self.analysis_prompt | self.llm
        response = chain.invoke({
            "query": query,
            "iteration": iteration + 1,
            "previous_analysis": previous_analysis_text,
            "search_results": formatted_results
        })
        
        analysis_text = response.content
        
        # 更新分析内容
        state["analysis"] = [analysis_text]
        state["current_step"] = f"第 {iteration + 1} 轮深度分析完成"
        state["messages"] = [f"🧠 Research Agent (第{iteration + 1}轮): 已完成深度分析，生成 {len(analysis_text)} 字分析报告"]
        
        # 评估是否需要更多研究
        if iteration + 1 < max_iterations:
            eval_chain = self.evaluation_prompt | self.llm
            eval_response = eval_chain.invoke({
                "query": query,
                "iteration": iteration + 1,
                "max_iterations": max_iterations,
                "analysis": analysis_text,
                "source_count": len(search_results)
            })
            
            # 解析评估结果
            try:
                eval_content = eval_response.content
                json_match = re.search(r'\{.*\}', eval_content, re.DOTALL)
                if json_match:
                    eval_result = json.loads(json_match.group())
                    state["need_more_research"] = eval_result.get("need_more_research", False)
                    state["additional_questions"] = eval_result.get("additional_questions", [])
                    
                    if state["need_more_research"]:
                        state["messages"] = [f"💡 Research Agent: 发现信息缺口，需要进一步研究 {len(state['additional_questions'])} 个问题"]
                    else:
                        state["messages"] = [f"✅ Research Agent: 信息已充分，可以生成最终报告"]
                else:
                    state["need_more_research"] = False
                    state["additional_questions"] = []
            except Exception as e:
                print(f"评估解析错误: {e}")
                state["need_more_research"] = False
                state["additional_questions"] = []
        else:
            # 已达到最大迭代次数
            state["need_more_research"] = False
            state["additional_questions"] = []
            state["messages"] = [f"🔄 Research Agent: 已完成 {max_iterations} 轮研究，准备生成报告"]
        
        return state


# 创建Research Agent实例
research_agent = ResearchAgent()
