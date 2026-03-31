"""
LangGraph状态定义
定义工作流中的状态结构
"""
from typing import TypedDict, List, Dict, Annotated
import operator


class ResearchState(TypedDict):
    """深度研究系统的状态"""
    
    # 用户输入
    query: str  # 用户的研究查询
    
    # 研究计划
    research_plan: List[str]  # Supervisor制定的研究主题列表
    
    # 搜索结果
    search_results: Annotated[List[Dict[str, str]], operator.add]  # 累积的搜索结果
    
    # 分析内容
    analysis: Annotated[List[str], operator.add]  # Research Agent的分析结果
    
    # 最终报告
    final_report: str  # Writer Agent生成的最终报告
    
    # 进度信息
    current_step: str  # 当前执行步骤
    iteration_count: int  # 迭代次数
    max_iterations: int  # 最大迭代次数
    
    # 循环控制
    need_more_research: bool  # 是否需要更多研究
    additional_questions: List[str]  # 需要进一步研究的问题
    
    # 消息历史
    messages: Annotated[List[str], operator.add]  # 各Agent的工作日志
