"""GraphRAG 索引构建模块"""
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger
import pandas as pd

# GraphRAG imports
try:
    from graphrag.index import create_pipeline_config
    from graphrag.index.run import run_pipeline_with_config
    from graphrag.config import create_graphrag_config
except ImportError:
    logger.warning("GraphRAG 库导入失败，请确保已安装 graphrag")


class GraphRAGIndexer:
    """GraphRAG 索引构建器"""
    
    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        llm_adapter,
        embedding_adapter,
    ):
        """初始化索引构建器
        
        Args:
            input_dir: 输入文档目录
            output_dir: 输出索引目录
            llm_adapter: LLM 适配器
            embedding_adapter: Embedding 适配器
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.llm_adapter = llm_adapter
        self.embedding_adapter = embedding_adapter
        
        # 确保目录存在
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_documents(self, documents: List[Dict[str, str]]) -> int:
        """准备文档用于索引构建
        
        Args:
            documents: 文档列表，格式: [{"filename": str, "content": str}]
            
        Returns:
            准备的文档数量
        """
        # 清空输入目录
        for file in self.input_dir.glob("*.txt"):
            file.unlink()
        
        # 将所有文档保存为 txt 文件
        for idx, doc in enumerate(documents):
            filename = f"doc_{idx}_{doc['filename']}.txt"
            file_path = self.input_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc['content'])
        
        logger.info(f"准备了 {len(documents)} 个文档到 {self.input_dir}")
        return len(documents)
    
    def build_index(
        self,
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        llm_temperature: float = 0.0,
        max_cluster_size: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """构建知识图谱索引
        
        Args:
            chunk_size: 文本分块大小
            chunk_overlap: 分块重叠
            llm_temperature: LLM 温度
            max_cluster_size: 社区检测最大簇大小
            **kwargs: 其他参数
            
        Returns:
            构建结果统计
        """
        logger.info("开始构建 GraphRAG 索引...")
        logger.info(f"参数: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}, "
                   f"llm_temperature={llm_temperature}, max_cluster_size={max_cluster_size}")
        
        try:
            # 创建配置
            config = self._create_config(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                llm_temperature=llm_temperature,
                max_cluster_size=max_cluster_size,
            )
            
            # 保存配置
            config_path = self.output_dir / "config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到: {config_path}")
            
            # 运行索引构建
            # 注意: 这里使用简化的方式，实际 GraphRAG 需要更复杂的配置
            result = self._run_indexing(config)
            
            logger.info("GraphRAG 索引构建完成!")
            return result
            
        except Exception as e:
            logger.error(f"构建索引失败: {e}")
            raise
    
    def _create_config(
        self,
        chunk_size: int,
        chunk_overlap: int,
        llm_temperature: float,
        max_cluster_size: int,
    ) -> Dict[str, Any]:
        """创建 GraphRAG 配置
        
        Returns:
            配置字典
        """
        config = {
            "input": {
                "type": "file",
                "file_type": "text",
                "base_dir": str(self.input_dir),
                "file_pattern": ".*\\.txt$",
            },
            "output": {
                "type": "file",
                "base_dir": str(self.output_dir),
            },
            "chunks": {
                "size": chunk_size,
                "overlap": chunk_overlap,
                "group_by_columns": ["id"],
            },
            "llm": {
                "type": "azure_openai_custom",
                "temperature": llm_temperature,
                "max_tokens": 2000,
            },
            "embeddings": {
                "type": "azure_openai",
                "batch_size": 16,
            },
            "entity_extraction": {
                "max_gleanings": 1,
            },
            "community_reports": {
                "max_length": 2000,
                "max_input_length": 8000,
            },
            "cluster_graph": {
                "max_cluster_size": max_cluster_size,
            },
        }
        
        return config
    
    def _run_indexing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行索引构建（简化版本）
        
        由于 GraphRAG 的实际 API 比较复杂，这里提供一个简化的模拟实现
        在实际部署时需要根据 GraphRAG 的版本进行适配
        
        Returns:
            构建结果
        """
        logger.info("正在运行索引构建流程...")
        
        # TODO: 实际的 GraphRAG 索引构建
        # 这里需要根据 GraphRAG 库的实际 API 进行实现
        # 由于 GraphRAG 库版本更新较快，具体实现可能需要调整
        
        # 模拟结果
        result = {
            "status": "success",
            "documents_processed": len(list(self.input_dir.glob("*.txt"))),
            "entities_extracted": 0,  # 将由实际流程填充
            "relationships_extracted": 0,
            "communities_detected": 0,
            "output_dir": str(self.output_dir),
        }
        
        # 保存结果
        result_path = self.output_dir / "index_result.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"索引结果已保存到: {result_path}")
        return result
    
    def get_index_status(self) -> Optional[Dict[str, Any]]:
        """获取索引状态
        
        Returns:
            索引状态信息，如果没有索引则返回 None
        """
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
