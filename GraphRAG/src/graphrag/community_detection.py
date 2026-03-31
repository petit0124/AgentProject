"""社区检测模块 - 使用Leiden算法进行图聚类"""
import networkx as nx
from typing import List, Dict, Any
from loguru import logger

try:
    from graspologic.partition import hierarchical_leiden
    HAS_GRASPOLOGIC = True
except ImportError:
    HAS_GRASPOLOGIC = False
    logger.warning("graspologic未安装，将使用简化的社区检测算法")


class CommunityDetector:
    """社区检测器"""
    
    def __init__(self, llm_adapter):
        """初始化社区检测器
        
        Args:
            llm_adapter: LLM适配器（用于生成社区摘要）
        """
        self.llm_adapter = llm_adapter
    
    def detect_communities(
        self,
        graph: nx.Graph,
        max_cluster_size: int = 10
    ) -> List[Dict[str, Any]]:
        """检测图中的社区
        
        Args:
            graph: NetworkX图对象
            max_cluster_size: 最大簇大小
            
        Returns:
            社区列表
        """
        logger.info(f"开始社区检测，图包含 {graph.number_of_nodes()} 个节点...")
        
        if graph.number_of_nodes() == 0:
            logger.warning("图为空，无法进行社区检测")
            return []
        
        try:
            if HAS_GRASPOLOGIC and graph.number_of_nodes() > 1:
                # 使用Leiden算法
                communities = self._leiden_detection(graph, max_cluster_size)
            else:
                # 使用简化算法（Louvain）
                communities = self._louvain_detection(graph)
            
            logger.info(f"检测到 {len(communities)} 个社区")
            return communities
            
        except Exception as e:
            logger.error(f"社区检测失败: {e}")
            # 降级：所有节点作为一个社区
            return self._fallback_single_community(graph)
    
    def _leiden_detection(
        self,
        graph: nx.Graph,
        max_cluster_size: int
    ) -> List[Dict[str, Any]]:
        """使用Leiden算法检测社区"""
        logger.info("使用Leiden算法...")
        
        # Leiden算法需要将图转换为adjacency matrix
        try:
            communities_dict = hierarchical_leiden(
                graph,
                max_cluster_size=max_cluster_size,
                random_seed=42
            )
            
            # 将结果转换为社区列表
            communities = self._dict_to_communities(communities_dict, graph)
            return communities
            
        except Exception as e:
            logger.error(f"Leiden算法失败: {e}")
            return self._louvain_detection(graph)
    
    def _louvain_detection(self, graph: nx.Graph) -> List[Dict[str, Any]]:
        """使用Louvain算法检测社区（备用方案）"""
        logger.info("使用Louvain算法...")
        
        try:
            import community as community_louvain
            
            # Louvain算法
            partition = community_louvain.best_partition(graph)
            
            # 按社区ID分组节点
            communities_map = {}
            for node, comm_id in partition.items():
                if comm_id not in communities_map:
                    communities_map[comm_id] = []
                communities_map[comm_id].append(node)
            
            # 转换为社区列表
            communities = []
            for comm_id, nodes in communities_map.items():
                communities.append({
                    "id": f"community_{comm_id}",
                    "nodes": nodes,
                    "size": len(nodes)
                })
            
            return communities
            
        except ImportError:
            logger.warning("python-louvain未安装，使用连通分量作为社区")
            return self._connected_components_detection(graph)
    
    def _connected_components_detection(self, graph: nx.Graph) -> List[Dict[str, Any]]:
        """使用连通分量作为社区（最基本的方案）"""
        logger.info("使用连通分量检测...")
        
        communities = []
        for i, component in enumerate(nx.connected_components(graph)):
            communities.append({
                "id": f"community_{i}",
                "nodes": list(component),
                "size": len(component)
            })
        
        return communities
    
    def _fallback_single_community(self, graph: nx.Graph) -> List[Dict[str, Any]]:
        """降级方案：所有节点作为一个社区"""
        logger.info("使用单一社区（降级方案）")
        
        return [{
            "id": "community_0",
            "nodes": list(graph.nodes()),
            "size": graph.number_of_nodes()
        }]
    
    def _dict_to_communities(
        self,
        communities_dict: Dict[int, int],
        graph: nx.Graph
    ) -> List[Dict[str, Any]]:
        """将字典格式的社区结果转换为列表格式"""
        communities_map = {}
        for node, comm_id in communities_dict.items():
            if comm_id not in communities_map:
                communities_map[comm_id] = []
            communities_map[comm_id].append(node)
        
        communities = []
        for comm_id, nodes in communities_map.items():
            communities.append({
                "id": f"community_{comm_id}",
                "nodes": nodes,
                "size": len(nodes)
            })
        
        return communities
    
    async def generate_community_summary(
        self,
        community: Dict[str, Any],
        graph: nx.Graph
    ) -> str:
        """为社区生成摘要
        
        Args:
            community: 社区信息
            graph: NetworkX图对象
            
        Returns:
            社区摘要文本
        """
        community_id = community["id"]
        nodes = community["nodes"]
        
        logger.info(f"为社区 {community_id} 生成摘要（包含 {len(nodes)} 个实体）...")
        
        try:
            # 收集社区内的实体信息
            entities_info = []
            for node in nodes:
                node_data = graph.nodes[node]
                entities_info.append({
                    "name": node_data.get("name", f"Entity_{node}"),
                    "type": node_data.get("type", "OTHER"),
                    "description": node_data.get("description", "")
                })
            
            # 收集社区内的关系
            relationships_info = []
            for source, target in graph.edges():
                if source in nodes and target in nodes:
                    edge_data = graph[source][target]
                    relationships_info.append({
                        "source": graph.nodes[source].get("name", f"Entity_{source}"),
                        "target": graph.nodes[target].get("name", f"Entity_{target}"),
                        "type": edge_data.get("type", "RELATED_TO"),
                        "description": edge_data.get("description", "")
                    })
            
            # 构建prompt
            prompt = self._build_summary_prompt(entities_info, relationships_info)
            
            # 调用LLM生成摘要
            summary = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=self._get_summary_system_prompt(),
                temperature=0.0,
            )
            
            logger.info(f"社区 {community_id} 摘要已生成")
            return summary
            
        except Exception as e:
            logger.error(f"社区摘要生成失败: {e}")
            return f"社区包含 {len(nodes)} 个实体"
    
    def _get_summary_system_prompt(self) -> str:
        """获取摘要生成的系统prompt"""
        return """你是一个专业的知识图谱分析助手。你的任务是为一个实体社区生成简洁的摘要。

要求：
1分析社区中的实体和它们之间的关系
2. 识别社区的主要主题和核心内容
3. 生成2-3段文字的摘要，突出重点
4. 使用清晰、简洁的语言"""
    
    def _build_summary_prompt(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> str:
        """构建社区摘要生成prompt"""
        # 格式化实体信息
        entities_text = "\n".join([
            f"- {e['name']} ({e['type']}): {e['description']}"
            for e in entities[:20]  # 限制数量避免prompt过长
        ])
        
        # 格式化关系信息
        relationships_text = "\n".join([
            f"- {r['source']} --[{r['type']}]--> {r['target']}"
            for r in relationships[:20]
        ])
        
        prompt = f"""请为以下实体社区生成一个简洁的摘要。

## 社区中的实体
{entities_text}

## 实体之间的关系
{relationships_text}

## 任务
请分析这个社区，并生成一个2-3段文字的摘要，描述：
1. 这个社区的主要主题是什么
2. 包含哪些核心实体和概念
3. 实体之间有什么重要的关系

摘要应该简洁清晰，帮助用户快速理解这个知识社区的内容。"""
        
        return prompt
