"""简化版 RAG 查询 - 基于向量相似度检索"""
import json
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger
import numpy as np


class SimpleRAGQuery:
    """简化版 RAG 查询器
    
    基于向量相似度进行文档检索
    """
    
    def __init__(
        self,
        index_dir: Path,
        llm_adapter,
        embedding_adapter,
    ):
        self.index_dir = Path(index_dir)
        self.llm_adapter = llm_adapter
        self.embedding_adapter = embedding_adapter
        
        # 加载索引
        self.index_data = None
        self._load_index()
    
    def _load_index(self):
        """加载索引数据"""
        index_path = self.index_dir / "simple_index.json"
        
        if not index_path.exists():
            logger.warning("索引文件不存在，请先构建索引")
            return
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                self.index_data = json.load(f)
            logger.info(f"成功加载索引，包含 {len(self.index_data['chunks'])} 个文本块")
        except Exception as e:
            logger.error(f"加载索引失败: {e}")
            self.index_data = None
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        temperature: float = 0.0,
        **kwargs
    ) -> Dict[str, Any]:
        """执行检索查询"""
        logger.info(f"执行检索: {query}")
        logger.info(f"参数: top_k={top_k}, temperature={temperature}")
        
        # 动态重新加载索引，确保使用最新的索引数据
        self._load_index()
        
        if not self.index_data:
            logger.error("索引未加载，无法执行查询")
            return {
                "query": query,
                "answer": "索引未构建，请先在知识图谱构建页面构建索引。",
                "chunks": [],
                "context_used": ""
            }
        
        try:
            # 1. 生成查询向量
            query_embedding = self.embedding_adapter.embed(query)
            
            # 2. 计算相似度并排序
            similarities = []
            chunks = self.index_data['chunks']
            embeddings = self.index_data['embeddings']
            
            for idx, chunk_embedding in enumerate(embeddings):
                similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                similarities.append((idx, similarity))
            
            # 按相似度排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = [idx for idx, _ in similarities[:top_k]]
            
            # 3. 获取最相关的文本块
            relevant_chunks = [chunks[idx] for idx in top_indices]
            
            # 4. 构建上下文
            context = self._build_context(relevant_chunks)
            
            # 5. 使用 LLM 生成答案
            answer = self._generate_answer(query, context, temperature)
            
            result = {
                "query": query,
                "answer": answer,
                "chunks": [
                    {
                        "text": chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'],
                        "source": chunk['source'],
                        "similarity": similarities[i][1]
                    }
                    for i, chunk in enumerate(relevant_chunks)
                ],
                "context_used": context[:500] + "..." if len(context) > 500 else context,
            }
            
            logger.info("检索完成")
            return result
            
        except Exception as e:
            logger.error(f"检索失败: {e}")
            logger.exception(e)
            return {
                "query": query,
                "answer": f"检索出错: {str(e)}",
                "chunks": [],
                "context_used": ""
            }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """从文本块构建上下文"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get('source', '未知来源')
            text = chunk.get('text', '')
            context_parts.append(f"[文档片段 {i} - 来源: {source}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def _generate_answer(
        self,
        query: str,
        context: str,
        temperature: float
    ) -> str:
        """使用 LLM 生成答案"""
        system_prompt = """你是一个专业的文档问答助手。你的任务是基于提供的文档片段，准确、全面地回答用户的问题。

要求：
1. 仅基于提供的文档片段回答，不要添加文档中没有的信息
2. 如果文档片段中没有相关信息，请明确告知用户
3. 回答要简洁清晰，突出重点
4. 如果有多个片段提供了相关信息，请综合所有片段给出完整答案"""
        
        prompt = f"""## 参考文档片段

{context}

---

## 用户问题
{query}

## 回答要求
请基于上述文档片段，准确回答用户的问题。如果文档中没有相关信息，请明确说明。"""
        
        try:
            answer = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
            )
            return answer
        except Exception as e:
            logger.error(f"生成答案失败: {e}")
            return f"生成答案时出错: {str(e)}"
