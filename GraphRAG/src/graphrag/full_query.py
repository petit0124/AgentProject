"""完整的 GraphRAG 查询器 - 支持本地和全局检索"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger

from .graph_builder import KnowledgeGraphBuilder


class FullGraphRAGQuery:
    """完整的 GraphRAG 查询器
    
    支持两种检索模式：
    - 本地检索：基于实体和关系，适合精确问答
    - 全局检索：基于社区摘要，适合宏观理解
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
        self.graph_builder = None
        self.communities = []
        self.summaries = {}
        self.chunks = []
        self.embeddings = []
        
        self._load_index()
    
    def _load_index(self):
        """加载索引数据"""
        logger.info("加载 GraphRAG 索引...")
        
        # 加载图
        graph_path = self.index_dir / "graph.json"
        if graph_path.exists():
            with open(graph_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            self.graph_builder = KnowledgeGraphBuilder.from_dict(graph_data)
            logger.info(f"已加载图: {self.graph_builder.graph.number_of_nodes()} 个节点, {self.graph_builder.graph.number_of_edges()} 条边")
        
        # 加载社区
        communities_path = self.index_dir / "communities.json"
        if communities_path.exists():
            with open(communities_path, 'r', encoding='utf-8') as f:
                communities_data = json.load(f)
            self.communities = communities_data.get("communities", [])
            self.summaries = communities_data.get("summaries", {})
            logger.info(f"已加载 {len(self.communities)} 个社区")
        
        # 加载文本块
        chunks_path = self.index_dir / "chunks.json"
        if chunks_path.exists():
            with open(chunks_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            logger.info(f"已加载 {len(self.chunks)} 个文本块")
        
        # 加载embeddings
        embeddings_path = self.index_dir / "embeddings.json"
        if embeddings_path.exists():
            with open(embeddings_path, 'r', encoding='utf-8') as f:
                self.embeddings = json.load(f)
            logger.info(f"已加载 {len(self.embeddings)} 个embeddings")
    
    def local_search(
        self,
        query: str,
        top_k: int = 5,
        temperature: float = 0.0,
        **kwargs
    ) -> Dict[str, Any]:
        """本地检索 - 基于实体和关系
        
        适合：需要精确实体信息的问题
        例如："某人做了什么？"、"A和B有什么关系？"
        """
        logger.info(f"执行本地检索: {query}")
        logger.info(f"参数: top_k={top_k}, temperature={temperature}")
        
        # 重新加载索引以确保最新
        self._load_index()
        
        if not self.graph_builder:
            return {
                "query": query,
                "search_type": "local",
                "answer": "索引未构建，请先构建 GraphRAG 索引。",
                "entities": [],
                "relationships": [],
                "context_used": ""
            }
        
        try:
            # 1. 从查询中提取实体
            query_entities = self._extract_query_entities(query)
            logger.info(f"查询中识别的实体: {query_entities}")
            
            # 2. 在图中查找相关实体和关系
            related_entities, related_relationships = self._find_related_in_graph(
                query_entities,
                top_k
            )
            
            # 3. 构建上下文
            context = self._build_local_context(related_entities, related_relationships)
            
            # 4. 使用LLM生成答案
            answer = self._generate_answer(query, context, temperature, "local")
            
            return {
                "query": query,
                "search_type": "local",
                "answer": answer,
                "entities": related_entities,
                "relationships": related_relationships,
                "context_used": context[:500] + "..." if len(context) > 500 else context,
            }
            
        except Exception as e:
            logger.error(f"本地检索失败: {e}")
            logger.exception(e)
            return {
                "query": query,
                "search_type": "local",
                "answer": f"检索出错: {str(e)}",
                "entities": [],
                "relationships": [],
                "context_used": ""
            }
    
    def global_search(
        self,
        query: str,
        top_k: int = 5,
        temperature: float = 0.0,
        **kwargs
    ) -> Dict[str, Any]:
        """全局检索 - 基于社区摘要
        
        适合：需要整体理解的问题
        例如："文档的主要内容是什么？"、"整体趋势是什么？"
        """
        logger.info(f"执行全局检索: {query}")
        logger.info(f"参数: top_k={top_k}, temperature={temperature}")
        
        # 重新加载索引
        self._load_index()
        
        if not self.communities:
            return {
                "query": query,
                "search_type": "global",
                "answer": "索引未构建，请先构建 GraphRAG 索引。",
                "communities": [],
                "context_used": ""
            }
        
        try:
            # 1. 找到最相关的社区
            relevant_communities = self._find_relevant_communities(query, top_k)
            
            # 2. 构建上下文（使用社区摘要）
            context = self._build_global_context(relevant_communities)
            
            # 3. 使用LLM生成答案
            answer = self._generate_answer(query, context, temperature, "global")
            
            return {
                "query": query,
                "search_type": "global",
                "answer": answer,
                "communities": relevant_communities,
                "context_used": context[:500] + "..." if len(context) > 500 else context,
            }
            
        except Exception as e:
            logger.error(f"全局检索失败: {e}")
            logger.exception(e)
            return {
                "query": query,
                "search_type": "global",
                "answer": f"检索出错: {str(e)}",
                "communities": [],
                "context_used": ""
            }
    
    def _extract_query_entities(self, query: str) -> List[str]:
        """从查询中提取实体名称（简化版）"""
        # 在图中查找匹配的实体
        query_lower = query.lower()
        matched_entities = []
        
        for entity_name in self.graph_builder.entity_index.keys():
            if entity_name.lower() in query_lower or query_lower in entity_name.lower():
                matched_entities.append(entity_name)
        
        return matched_entities[:5]  # 限制数量
    
    def _find_related_in_graph(
        self,
        query_entities: List[str],
        top_k: int
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """在图中查找相关实体和关系"""
        all_entities = set()
        all_relationships = []
        
        # 如果查询中有实体，获取它们的邻居
        if query_entities:
            for entity_name in query_entities:
                entity = self.graph_builder.get_entity_by_name(entity_name)
                if entity:
                    all_entities.add(entity['id'])
                    
                    # 获取邻居
                    neighbors = self.graph_builder.get_neighbors(entity_name, max_depth=1)
                    for neighbor in neighbors[:top_k]:
                        all_entities.add(neighbor['id'])
        else:
            # 如果没有找到实体，返回度数最高的节点
            degree_sorted = sorted(
                self.graph_builder.graph.degree(),
                key=lambda x: x[1],
                reverse=True
            )
            for node_id, _ in degree_sorted[:top_k]:
                all_entities.add(node_id)
        
        # 获取实体详情
        entities_info = []
        for entity_id in all_entities:
            entities_info.append({
                "id": entity_id,
                **self.graph_builder.graph.nodes[entity_id]
            })
        
        # 获取这些实体之间的关系
        for source in all_entities:
            for target in all_entities:
                if source != target and self.graph_builder.graph.has_edge(source, target):
                    edge_data = self.graph_builder.graph[source][target]
                    all_relationships.append({
                        "source": self.graph_builder.graph.nodes[source]['name'],
                        "target": self.graph_builder.graph.nodes[target]['name'],
                        **edge_data
                    })
        
        return entities_info[:top_k], all_relationships[:top_k * 2]
    
    def _find_relevant_communities(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """找到最相关的社区（基于摘要的相似度）"""
        if not self.summaries:
            return self.communities[:top_k]
        
        # 生成查询的embedding
        query_embedding = self.embedding_adapter.embed(query)
        
        # 为每个社区摘要生成embedding并计算相似度
        community_scores = []
        for community in self.communities:
            comm_id = community['id']
            summary = self.summaries.get(comm_id, "")
            
            if summary:
                summary_embedding = self.embedding_adapter.embed(summary)
                similarity = self._cosine_similarity(query_embedding, summary_embedding)
                community_scores.append((community, similarity))
        
        # 按相似度排序
        community_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 返回top-k社区
        relevant = []
        for community, score in community_scores[:top_k]:
            relevant.append({
                **community,
                "summary": self.summaries.get(community['id'], ""),
                "similarity": score
            })
        
        return relevant
    
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
    
    def _build_local_context(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> str:
        """构建本地检索的上下文"""
        context_parts = []
        
        # 添加实体信息
        if entities:
            context_parts.append("## 相关实体\n")
            for entity in entities:
                context_parts.append(
                    f"- **{entity['name']}** ({entity.get('type', 'OTHER')}): {entity.get('description', '无描述')}"
                )
        
        # 添加关系信息
        if relationships:
            context_parts.append("\n## 实体之间的关系\n")
            for rel in relationships:
                context_parts.append(
                    f"- {rel['source']} --[{rel.get('type', 'RELATED_TO')}]--> {rel['target']}"
                )
                if rel.get('description'):
                    context_parts.append(f"  ({rel['description']})")
        
        return "\n".join(context_parts)
    
    def _build_global_context(
        self,
        communities: List[Dict[str, Any]]
    ) -> str:
        """构建全局检索的上下文"""
        context_parts = []
        
        for i, community in enumerate(communities, 1):
            context_parts.append(f"## 知识社区 {i}\n")
            context_parts.append(f"**规模**: {community.get('size', 0)} 个实体\n")
            context_parts.append(f"**摘要**: {community.get('summary', '无摘要')}\n")
        
        return "\n".join(context_parts)
    
    def _generate_answer(
        self,
        query: str,
        context: str,
        temperature: float,
        search_type: str
    ) -> str:
        """使用LLM生成答案"""
        if search_type == "local":
            system_prompt = """你是一个专业的知识图谱问答助手。基于提供的实体和关系信息，准确回答用户的问题。

要求：
1. 仅基于提供的实体和关系回答
2. 如果信息不足，明确告知用户
3. 回答要准确、具体"""
        else:
            system_prompt = """你是一个专业的知识图谱问答助手。基于提供的知识社区摘要，从整体角度回答用户的问题。

要求：
1. 综合多个社区的信息
2. 提供全局性的理解和见解
3. 回答要完整、有条理"""
        
        prompt = f"""## 知识图谱信息

{context}

---

## 用户问题
{query}

## 回答要求
请基于上述知识图谱信息，准确回答用户的问题。"""
        
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
