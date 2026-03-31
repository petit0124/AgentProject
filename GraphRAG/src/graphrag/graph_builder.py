"""知识图谱构建模块"""
import networkx as nx
from typing import List, Dict, Any, Set, Tuple, Optional
from loguru import logger


class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self):
        """初始化图构建器"""
        self.graph = nx.Graph()
        self.entity_index = {}  # 实体名称到ID的映射
        self.next_id = 0
    
    def add_entities(self, entities: List[Dict[str, Any]]):
        """添加实体到图中
        
        Args:
            entities: 实体列表
        """
        logger.info(f"添加 {len(entities)} 个实体到图中...")
        
        for entity in entities:
            entity_name = entity["name"]
            
            # 如果实体已存在，更新属性
            if entity_name in self.entity_index:
                entity_id = self.entity_index[entity_name]
                # 更新节点属性
                self.graph.nodes[entity_id].update({
                    "type": entity.get("type", "OTHER"),
                    "description": entity.get("description", ""),
                })
            else:
                # 创建新节点
                entity_id = self.next_id
                self.next_id += 1
                
                self.graph.add_node(
                    entity_id,
                    name=entity_name,
                    type=entity.get("type", "OTHER"),
                    description=entity.get("description", ""),
                    source_chunks=entity.get("source_chunks", [entity.get("source_chunk", "")])
                )
                
                self.entity_index[entity_name] = entity_id
        
        logger.info(f"图中现有 {self.graph.number_of_nodes()} 个节点")
    
    def add_relationships(self, relationships: List[Dict[str, Any]]):
        """添加关系到图中
        
        Args:
            relationships: 关系列表
        """
        logger.info(f"添加 {len(relationships)} 个关系到图中...")
        
        added_count = 0
        for rel in relationships:
            source_name = rel["source"]
            target_name = rel["target"]
            
            # 确保源和目标实体都存在
            if source_name not in self.entity_index or target_name not in self.entity_index:
                logger.warning(f"关系中的实体不存在: {source_name} -> {target_name}")
                continue
            
            source_id = self.entity_index[source_name]
            target_id = self.entity_index[target_name]
            
            # 添加边
            if not self.graph.has_edge(source_id, target_id):
                self.graph.add_edge(
                    source_id,
                    target_id,
                    type=rel.get("type", "RELATED_TO"),
                    description=rel.get("description", ""),
                    weight=1.0
                )
                added_count += 1
            else:
                # 如果边已存在，增加权重
                self.graph[source_id][target_id]["weight"] += 1.0
        
        logger.info(f"成功添加 {added_count} 条边，图中现有 {self.graph.number_of_edges()} 条边")
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """获取图的统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0,
            "entity_types": self._count_entity_types(),
            "relationship_types": self._count_relationship_types(),
        }
        
        # 连通分量
        if self.graph.number_of_nodes() > 0:
            stats["num_connected_components"] = nx.number_connected_components(self.graph)
        
        return stats
    
    def _count_entity_types(self) -> Dict[str, int]:
        """统计实体类型分布"""
        type_counts = {}
        for node_id in self.graph.nodes():
            node_type = self.graph.nodes[node_id].get("type", "OTHER")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        return type_counts
    
    def _count_relationship_types(self) -> Dict[str, int]:
        """统计关系类型分布"""
        type_counts = {}
        for source, target in self.graph.edges():
            rel_type = self.graph[source][target].get("type", "RELATED_TO")
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        return type_counts
    
    def get_entity_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取实体
        
        Args:
            name: 实体名称
            
        Returns:
            实体信息，如果不存在返回None
        """
        if name not in self.entity_index:
            return None
        
        entity_id = self.entity_index[name]
        return {
            "id": entity_id,
            **self.graph.nodes[entity_id]
        }
    
    def get_neighbors(self, entity_name: str, max_depth: int = 1) -> List[Dict[str, Any]]:
        """获取实体的邻居
        
        Args:
            entity_name: 实体名称
            max_depth: 最大深度
            
        Returns:
            邻居实体列表
        """
        if entity_name not in self.entity_index:
            return []
        
        entity_id = self.entity_index[entity_name]
        neighbors = []
        
        # 获取指定深度内的所有邻居
        visited = set([entity_id])
        current_level = [entity_id]
        
        for depth in range(max_depth):
            next_level = []
            for node in current_level:
                for neighbor in self.graph.neighbors(node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.append(neighbor)
                        neighbors.append({
                            "id": neighbor,
                            "depth": depth + 1,
                            **self.graph.nodes[neighbor]
                        })
            current_level = next_level
        
        return neighbors
    
    def to_dict(self) -> Dict[str, Any]:
        """将图转换为字典格式
        
        Returns:
            图的字典表示
        """
        nodes = [
            {"id": node_id, **self.graph.nodes[node_id]}
            for node_id in self.graph.nodes()
        ]
        
        edges = [
            {
                "source": source,
                "target": target,
                **self.graph[source][target]
            }
            for source, target in self.graph.edges()
        ]
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": self.get_graph_stats()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGraphBuilder':
        """从字典创建图
        
        Args:
            data: 图的字典表示
            
        Returns:
            KnowledgeGraphBuilder实例
        """
        builder = cls()
        
        # 添加节点
        for node in data.get("nodes", []):
            node_id = node["id"]
            builder.graph.add_node(node_id, **{k: v for k, v in node.items() if k != "id"})
            builder.entity_index[node["name"]] = node_id
            builder.next_id = max(builder.next_id, node_id + 1)
        
        # 添加边
        for edge in data.get("edges", []):
            builder.graph.add_edge(
                edge["source"],
                edge["target"],
                **{k: v for k, v in edge.items() if k not in ["source", "target"]}
            )
        
        return builder
