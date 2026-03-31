"""配置管理模块"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    """应用配置管理"""
    
    def __init__(self):
        # Azure OpenAI LLM 配置
        self.llm_endpoint = os.getenv("LLM_ENDPOINT", "")
        self.llm_model = os.getenv("LLM_MODEL", "azure02-gpt-5")
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        
        # Azure OpenAI Embedding 配置
        self.embedding_endpoint = os.getenv("EMBEDDING_ENDPOINT", "")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "FXIAOKE-MODEL-text-embedding-ada-002")
        self.embedding_api_key = os.getenv("EMBEDDING_API_KEY", "")
        
        # 数据目录配置
        self.data_input_dir = Path(os.getenv("DATA_INPUT_DIR", "./data/input"))
        self.data_output_dir = Path(os.getenv("DATA_OUTPUT_DIR", "./data/output"))
        
        # 默认参数
        self.default_chunk_size = int(os.getenv("DEFAULT_CHUNK_SIZE", "300"))
        self.default_chunk_overlap = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "50"))
        self.default_llm_temperature = float(os.getenv("DEFAULT_LLM_TEMPERATURE", "0.0"))
        self.default_max_cluster_size = int(os.getenv("DEFAULT_MAX_CLUSTER_SIZE", "10"))
        
        # 确保数据目录存在
        self.data_input_dir.mkdir(parents=True, exist_ok=True)
        self.data_output_dir.mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """验证配置是否完整"""
        if not self.llm_endpoint:
            return False, "LLM_ENDPOINT 未配置"
        if not self.llm_api_key:
            return False, "LLM_API_KEY 未配置"
        if not self.embedding_endpoint:
            return False, "EMBEDDING_ENDPOINT 未配置"
        if not self.embedding_api_key:
            return False, "EMBEDDING_API_KEY 未配置"
        return True, None
    
    def get_graphrag_config(self) -> dict:
        """获取 GraphRAG 配置字典"""
        return {
            "llm": {
                "endpoint": self.llm_endpoint,
                "model": self.llm_model,
                "api_key": self.llm_api_key,
            },
            "embedding": {
                "endpoint": self.embedding_endpoint,
                "model": self.embedding_model,
                "api_key": self.embedding_api_key,
            },
            "storage": {
                "input_dir": str(self.data_input_dir),
                "output_dir": str(self.data_output_dir),
            },
            "defaults": {
                "chunk_size": self.default_chunk_size,
                "chunk_overlap": self.default_chunk_overlap,
                "llm_temperature": self.default_llm_temperature,
                "max_cluster_size": self.default_max_cluster_size,
            }
        }


# 全局配置实例
settings = Settings()
