"""
Web Fetcher Tool
负责从URL获取网页内容
"""
from langchain_community.document_loaders import WebBaseLoader
from typing import Optional

class WebFetcher:
    """网页内容获取工具"""
    
    def fetch(self, url: str) -> Optional[str]:
        """
        获取指定URL的网页内容
        
        Args:
            url: 目标网页URL
            
        Returns:
            网页文本内容，如果获取失败返回None
        """
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            if docs and len(docs) > 0:
                return docs[0].page_content
            return "未能获取到网页内容"
        except Exception as e:
            return f"获取网页内容时出错: {str(e)}"

# 创建全局实例
web_fetcher = WebFetcher()
