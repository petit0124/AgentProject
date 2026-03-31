"""
Tavily搜索工具
提供网络搜索能力
"""
import os
from typing import List, Dict
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()


class TavilySearch:
    """Tavily搜索工具封装"""
    
    def __init__(self):
        """初始化Tavily客户端"""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("未找到TAVILY_API_KEY环境变量")
        self.client = TavilyClient(api_key=api_key)
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        执行搜索查询
        
        Args:
            query: 搜索查询字符串
            max_results: 最大返回结果数
        
        Returns:
            搜索结果列表，每个结果包含title, url, content
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"  # 使用高级搜索获得更深入的结果
            )
            
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", "")
                })
            
            return results
        except Exception as e:
            print(f"搜索时出错: {str(e)}")
            return []
    
    def search_formatted(self, query: str, max_results: int = 5) -> str:
        """
        执行搜索并返回格式化的字符串结果
        
        Args:
            query: 搜索查询字符串
            max_results: 最大返回结果数
        
        Returns:
            格式化的搜索结果字符串
        """
        results = self.search(query, max_results)
        
        if not results:
            return "未找到相关搜索结果"
        
        formatted = f"搜索查询: {query}\n\n找到 {len(results)} 个结果:\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"【结果 {i}】\n"
            formatted += f"标题: {result['title']}\n"
            formatted += f"链接: {result['url']}\n"
            formatted += f"内容摘要: {result['content']}\n\n"
        
        return formatted


# 创建全局搜索实例
tavily_search = TavilySearch()
