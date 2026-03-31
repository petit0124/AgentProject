"""
Search Agent
负责网络检索，获取相关信息
"""
from src.tools.tavily_search import tavily_search
from src.graph.state import ResearchState


class SearchAgent:
    """Search Agent负责执行网络搜索"""
    
    def __init__(self):
        self.search_tool = tavily_search
        from src.tools.web_fetcher import web_fetcher
        self.fetch_tool = web_fetcher
    
    def search(self, state: ResearchState) -> ResearchState:
        """
        根据研究计划或补充问题执行搜索
        
        Args:
            state: 当前状态
        
        Returns:
            更新后的状态
        """
        iteration = state.get("iteration_count", 0)
        
        # 第一轮：使用研究计划
        if iteration == 0:
            research_plan = state.get("research_plan", [])
            search_topics = research_plan
            state["messages"] = [f"🔍 Search Agent (第1轮): 开始搜索 {len(search_topics)} 个研究主题"]
        else:
            # 后续轮次：使用补充问题
            additional_questions = state.get("additional_questions", [])
            search_topics = additional_questions
            state["messages"] = [f"🔍 Search Agent (第{iteration + 1}轮): 针对 {len(search_topics)} 个补充问题进行深度搜索"]
        
        all_results = []
        messages = []
        
        # 为每个主题执行搜索
        for i, topic in enumerate(search_topics, 1):
            messages.append(f"   正在搜索 {i}/{len(search_topics)}: {topic}")
            
            # 执行搜索
            results = self.search_tool.search(topic, max_results=3)
            
            # 将主题信息添加到结果中
            for result in results:
                result["search_topic"] = topic
                result["iteration"] = iteration + 1
                all_results.append(result)
            
            # 尝试获取第一条结果的详细内容
            if results and len(results) > 0:
                first_result = results[0]
                first_url = first_result.get("url")
                if first_url:
                    messages.append(f"   📥 正在获取详细内容: {first_url}")
                    # 限制内容长度，避免上下文过长
                    content = self.fetch_tool.fetch(first_url)
                    if content:
                        # 更新内容，保留前5000个字符
                        first_result["content"] = f"[以下是网页完整内容摘要]\n{content[:5000]}..."
                        first_result["has_full_content"] = True
                        messages.append(f"   ✓ 获取并更新了详细内容 ({len(content)} 字符)")
            
            messages.append(f"   ✓ 找到 {len(results)} 个相关结果")
        
        # 更新状态
        state["search_results"] = all_results
        state["current_step"] = f"第 {iteration + 1} 轮搜索完成，共找到 {len(all_results)} 个结果"
        state["messages"] = messages
        
        # 增加迭代计数
        state["iteration_count"] = iteration + 1
        
        return state


# 创建Search Agent实例
search_agent = SearchAgent()
