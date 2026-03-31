"""
LangGraph工作流
构建完整的研究工作流图
"""
from langgraph.graph import StateGraph, END
from src.graph.state import ResearchState
from src.agents.supervisor import supervisor_agent
from src.agents.search_agent import search_agent
from src.agents.research_agent import research_agent
from src.agents.writer_agent import writer_agent


def create_research_workflow():
    """
    创建支持多轮迭代的研究工作流图
    
    Returns:
        编译后的工作流图
    """
    # 创建状态图
    workflow = StateGraph(ResearchState)
    
    # 添加节点
    workflow.add_node("supervisor", supervisor_agent.create_plan)
    workflow.add_node("search", search_agent.search)
    workflow.add_node("research", research_agent.analyze)
    workflow.add_node("writer", writer_agent.write_report)
    
    # 定义条件路由函数
    def should_continue_research(state: ResearchState) -> str:
        """
        决定是否需要继续研究还是生成报告
        
        Returns:
            "search" - 继续搜索更多信息
            "writer" - 生成最终报告
        """
        need_more = state.get("need_more_research", False)
        iteration = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 1)
        
        # 如果需要更多研究且未达到最大迭代次数，继续搜索
        if need_more and iteration < max_iterations:
            return "search"
        else:
            return "writer"
    
    # 定义工作流边
    # START -> Supervisor
    workflow.set_entry_point("supervisor")
    
    # Supervisor -> Search (第一轮搜索)
    workflow.add_edge("supervisor", "search")
    
    # Search -> Research
    workflow.add_edge("search", "research")
    
    # Research -> 条件判断 (继续搜索 or 生成报告)
    workflow.add_conditional_edges(
        "research",
        should_continue_research,
        {
            "search": "search",  # 循环回搜索
            "writer": "writer"   # 进入报告生成
        }
    )
    
    # Writer -> END
    workflow.add_edge("writer", END)
    
    # 编译工作流
    app = workflow.compile()
    
    return app


def run_research(query: str, max_iterations: int = 1):
    """
    运行研究工作流
    
    Args:
        query: 用户查询
        max_iterations: 最大迭代次数
    
    Returns:
        最终状态
    """
    # 创建工作流
    app = create_research_workflow()
    
    # 初始化状态
    initial_state = {
        "query": query,
        "research_plan": [],
        "search_results": [],
        "analysis": [],
        "final_report": "",
        "current_step": "开始研究",
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "need_more_research": False,
        "additional_questions": [],
        "messages": []
    }
    
    # 运行工作流
    final_state = app.invoke(initial_state)
    
    return final_state


def stream_research(query: str, max_iterations: int = 1):
    """
    流式运行研究工作流，实时返回状态更新
    
    Args:
        query: 用户查询
        max_iterations: 最大迭代次数
    
    Yields:
        状态更新
    """
    # 创建工作流
    app = create_research_workflow()
    
    # 初始化状态
    initial_state = {
        "query": query,
        "research_plan": [],
        "search_results": [],
        "analysis": [],
        "final_report": "",
        "current_step": "开始研究",
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "need_more_research": False,
        "additional_questions": [],
        "messages": []
    }
    
    # 流式运行工作流
    for state in app.stream(initial_state):
        yield state
