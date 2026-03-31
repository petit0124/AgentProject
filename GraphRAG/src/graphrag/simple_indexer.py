"""简化版 RAG 索引构建 - 基于文档分块和向量检索"""
import json
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger
import numpy as np


class SimpleRAGIndexer:
    """简化版 RAG 索引构建器
    
    不依赖完整的GraphRAG库，实现基本的文档分块和向量索引功能
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
        
        logger.info(f"准备了 {len(documents)} 个文档到 {self.input_dir}")
        return len(documents)
    
    def build_index(
        self,
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """构建简化的向量索引"""
        logger.info("开始构建简化版 RAG 索引...")
        logger.info(f"参数: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        
        try:
            # 1. 读取所有文档
            documents = []
            for file_path in self.input_dir.glob("*.txt"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    documents.append({
                        "filename": file_path.name,
                        "content": content
                    })
            
            logger.info(f"读取了 {len(documents)} 个文档")
            
            # 2. 分块
            chunks = []
            for doc in documents:
                doc_chunks = self._chunk_text(
                    doc['content'], 
                    chunk_size, 
                    chunk_overlap,
                    doc['filename']
                )
                chunks.extend(doc_chunks)
            
            logger.info(f"生成了 {len(chunks)} 个文本块")
            
            # 3. 生成embeddings
            logger.info("正在生成文本块的embeddings...")
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedding_adapter.embed_batch(chunk_texts)
            
            # 4. 保存索引
            index_data = {
                "chunks": chunks,
                "embeddings": [emb for emb in embeddings],  # 转换为列表
                "metadata": {
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "num_documents": len(documents),
                    "num_chunks": len(chunks)
                }
            }
            
            index_path = self.output_dir / "simple_index.json"
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"索引已保存到: {index_path}")
            
            # 保存结果统计
            result = {
                "status": "success",
                "documents_processed": len(documents),
                "chunks_created": len(chunks),
                "index_type": "simple_rag",
                "output_dir": str(self.output_dir),
            }
            
            result_path = self.output_dir / "index_result.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info("简化版 RAG 索引构建完成!")
            return result
            
        except Exception as e:
            logger.error(f"构建索引失败: {e}")
            logger.exception(e)
            raise
    
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
            
            if chunk_text.strip():  # 忽略空块
                chunks.append({
                    "id": f"{source}_chunk_{chunk_id}",
                    "text": chunk_text,
                    "source": source,
                    "start": start,
                    "end": min(end, len(text))
                })
                chunk_id += 1
            
            start = end - chunk_overlap
            
            # 防止无限循环
            if chunk_overlap >= chunk_size:
                break
        
        return chunks
    
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
