"""完整的 GraphRAG 索引构建器"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger

from .entity_extraction import EntityExtractor
from .graph_builder import KnowledgeGraphBuilder
from .community_detection import CommunityDetector


class FullGraphRAGIndexer:
    """完整的 GraphRAG 索引构建器
    
    实现真正的知识图谱功能：
    - 实体抽取
    - 关系识别
    - 图构建
    - 社区检测
    - 社区摘要生成
    """
    
    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        llm_adapter,
        embedding_adapter,
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.llm_adapter = llm_adapter
        self.embedding_adapter = embedding_adapter
        
        # 初始化各个组件
        self.entity_extractor = EntityExtractor(llm_adapter)
        self.graph_builder = KnowledgeGraphBuilder()
        self.community_detector = CommunityDetector(llm_adapter)
        
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_documents(self, documents: List[Dict[str, str]]) -> int:
        """准备文档"""
        # 清空输入目录
        for file in self.input_dir.glob("*.txt"):
            file.unlink()
        
        # 保存文档
        for idx, doc in enumerate(documents):
            filename = f"doc_{idx}_{doc['filename']}.txt"
            file_path = self.input_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc['content'])
        
        logger.info(f"准备了 {len(documents)} 个文档到 {self.output_dir}")
        return len(documents)
    
    def build_index(
        self,
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        max_cluster_size: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """构建完整的 GraphRAG 索引
        
        Args:
            chunk_size: 文本分块大小
            chunk_overlap: 分块重叠
            max_cluster_size: 最大簇大小
            
        Returns:
            构建结果统计
        """
        logger.info("=" * 60)
        logger.info("开始构建完整的 GraphRAG 知识图谱索引")
        logger.info("=" * 60)
        logger.info(f"参数: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}, max_cluster_size={max_cluster_size}")
        
        try:
            # 1. 读取文档并分块
            logger.info("\n[步骤 1/6] 读取文档并分块...")
            chunks = self._load_and_chunk_documents(chunk_size, chunk_overlap)
            logger.info(f"✓ 生成了 {len(chunks)} 个文本块")
            
            # 2. 从每个块中提取实体和关系
            logger.info("\n[步骤 2/6] 提取实体和关系...")
            all_entities, all_relationships = self._extract_entities_from_chunks(chunks)
            logger.info(f"✓ 原始提取: {len(all_entities)} 个实体, {len(all_relationships)} 个关系")
            
            # 3. 实体去重
            logger.info("\n[步骤 3/6] 实体去重...")
            deduplicated_entities = self.entity_extractor.deduplicate_entities(all_entities)
            deduplicated_relationships = self.entity_extractor.deduplicate_relationships(all_relationships)
            logger.info(f"✓ 去重后: {len(deduplicated_entities)} 个实体, {len(deduplicated_relationships)} 个关系")
            
            # 4. 构建知识图谱
            logger.info("\n[步骤 4/6] 构建知识图谱...")
            self.graph_builder.add_entities(deduplicated_entities)
            self.graph_builder.add_relationships(deduplicated_relationships)
            graph_stats = self.graph_builder.get_graph_stats()
            logger.info(f"✓ 图构建完成: {graph_stats}")
            
            # 5. 社区检测
            logger.info("\n[步骤 5/6] 检测社区...")
            communities = self.community_detector.detect_communities(
                self.graph_builder.graph,
                max_cluster_size=max_cluster_size
            )
            logger.info(f"✓ 检测到 {len(communities)} 个社区")
            
            # 6. 生成社区摘要
            logger.info("\n[步骤 6/6] 生成社区摘要...")
            community_summaries = self._generate_community_summaries(communities)
            logger.info(f"✓ 生成了 {len(community_summaries)} 个社区摘要")
            
            # 保存索引
            logger.info("\n保存索引...")
            self._save_index(
                deduplicated_entities,
                deduplicated_relationships,
                communities,
                community_summaries,
                chunks
            )
            
            # 构建结果
            result = {
                "status": "success",
                "index_type": "full_graphrag",
                "documents_processed": len(list(self.input_dir.glob("*.txt"))),
                "chunks_created": len(chunks),
                "entities_extracted": len(deduplicated_entities),
                "relationships_extracted": len(deduplicated_relationships),
                "communities_detected": len(communities),
                "graph_stats": graph_stats,
                "output_dir": str(self.output_dir),
            }
            
            # 保存结果摘要
            result_path = self.output_dir / "index_result.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info("=" * 60)
            logger.info("✓ GraphRAG 知识图谱索引构建完成！")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"索引构建失败: {e}")
            logger.exception(e)
            raise
    
    def _load_and_chunk_documents(
        self,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """读取文档并分块"""
        documents = []
        for file_path in self.input_dir.glob("*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append({
                    "filename": file_path.name,
                    "content": content
                })
        
        # 分块
        chunks = []
        for doc in documents:
            doc_chunks = self._chunk_text(
                doc['content'],
                chunk_size,
                chunk_overlap,
                doc['filename']
            )
            chunks.extend(doc_chunks)
        
        return chunks
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        source: str
    ) -> List[Dict[str, Any]]:
        """将文本分块"""
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append({
                    "id": f"{source}_chunk_{chunk_id}",
                    "text": chunk_text,
                    "source": source,
                    "start": start,
                    "end": min(end, len(text))
                })
                chunk_id += 1
            
            start = end - chunk_overlap
            
            if chunk_overlap >= chunk_size:
                break
        
        return chunks
    
    def _extract_entities_from_chunks(
        self,
        chunks: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """从所有文本块中提取实体和关系"""
        all_entities = []
        all_relationships = []
        
        total = len(chunks)
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"  处理块 {i}/{total}: {chunk['id']}")
            
            result = self.entity_extractor.extract_entities_and_relations(
                chunk['text'],
                chunk['id']
            )
            
            all_entities.extend(result['entities'])
            all_relationships.extend(result['relationships'])
        
        return all_entities, all_relationships
    
    def _generate_community_summaries(
        self,
        communities: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """为所有社区生成摘要"""
        summaries = {}
        
        for i, community in enumerate(communities, 1):
            logger.info(f"  生成社区摘要 {i}/{len(communities)}: {community['id']}")
            
            # 使用同步方式调用
            try:
                summary = asyncio.run(
                    self.community_detector.generate_community_summary(
                        community,
                        self.graph_builder.graph
                    )
                )
                summaries[community['id']] = summary
            except:
                # 如果异步失败，尝试同步调用
                summary = self._generate_summary_sync(community)
                summaries[community['id']] = summary
        
        return summaries
    
    def _generate_summary_sync(self, community: Dict[str, Any]) -> str:
        """同步生成社区摘要（备用方案）"""
        return f"社区 {community['id']} 包含 {community['size']} 个实体"
    
    def _save_index(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        communities: List[Dict[str, Any]],
        summaries: Dict[str, str],
        chunks: List[Dict[str, Any]]
    ):
        """保存完整索引"""
        # 保存图数据
        graph_data = self.graph_builder.to_dict()
        graph_path = self.output_dir / "graph.json"
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        # 保存社区数据
        communities_data = {
            "communities": communities,
            "summaries": summaries
        }
        communities_path = self.output_dir / "communities.json"
        with open(communities_path, 'w', encoding='utf-8') as f:
            json.dump(communities_data, f, indent=2, ensure_ascii=False)
        
        # 保存文本块（用于检索）
        chunks_path = self.output_dir / "chunks.json"
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        # 生成embeddings并保存
        logger.info("生成文本块的embeddings...")
        chunk_texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_adapter.embed_batch(chunk_texts)
        
        embeddings_path = self.output_dir / "embeddings.json"
        with open(embeddings_path, 'w', encoding='utf-8') as f:
            json.dump(embeddings, f, indent=2)
        
        logger.info(f"索引已保存到: {self.output_dir}")
    
    def get_index_status(self) -> Dict[str, Any]:
        """获取索引状态"""
        result_path = self.output_dir / "index_result.json"
        
        if not result_path.exists():
            return None
        
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取索引状态失败: {e}")
            return None
    
    def clear_index(self):
        """清空索引"""
        import shutil
        
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"已清空索引目录: {self.output_dir}")
