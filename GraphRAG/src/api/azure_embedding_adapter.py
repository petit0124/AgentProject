"""Azure OpenAI Embedding 适配器"""
import json
import time
import os
import requests
from typing import List, Union, Optional
from loguru import logger
import numpy as np
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class AzureEmbeddingAdapter:
    """Azure OpenAI Embedding 适配器
    
    使用标准的 Azure OpenAI Embedding API
    使用 api-key 认证
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        timeout: int = 60,
        max_batch_size: int = 16,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        proxy: Optional[str] = None,
    ):
        """初始化 Embedding 适配器
        
        Args:
            endpoint: Azure OpenAI Embedding endpoint URL
            api_key: API key
            model: 模型名称
            timeout: 请求超时时间（秒）
            max_batch_size: 批处理最大大小
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒），会指数递增
            proxy: 代理服务器地址（格式：http://host:port），None表示使用系统代理或禁用
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_batch_size = max_batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 设置请求头
        self.headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
        }
        
        # 配置代理
        # 优先级：1. proxy参数 > 2. NO_PROXY/DISABLE_PROXY环境变量 > 3. HTTP_PROXY/HTTPS_PROXY环境变量 > 4. 默认禁用
        if proxy is not None:
            # 明确指定了proxy参数
            self.proxies = {"http": proxy, "https": proxy} if proxy else {}
        elif os.getenv("NO_PROXY") == "1" or os.getenv("DISABLE_PROXY") == "1":
            # 明确禁用代理
            self.proxies = {}
        elif os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY"):
            # 使用环境变量中的代理
            self.proxies = {
                "http": os.getenv("HTTP_PROXY"),
                "https": os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY"),
            }
        else:
            # 默认禁用代理（避免使用可能有问题的系统代理）
            self.proxies = {}
        
        # 创建带重试机制的session
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置代理
        if self.proxies:
            self.session.proxies.update(self.proxies)
            logger.debug(f"使用代理: {self.proxies}")
        else:
            # 明确禁用代理以避免使用系统代理
            # 使用空字典来禁用代理（None 会使用系统代理）
            self.session.proxies = {}
            logger.debug("已禁用代理")
    
    def embed(self, text: str) -> List[float]:
        """生成单个文本的 embedding
        
        Args:
            text: 输入文本
            
        Returns:
            Embedding 向量
        """
        return self.embed_batch([text])[0]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成 embedding
        
        Args:
            texts: 输入文本列表
            
        Returns:
            Embedding 向量列表
        """
        if not texts:
            return []
        
        # 分批处理
        all_embeddings = []
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            embeddings = self._embed_batch_internal(batch)
            all_embeddings.extend(embeddings)
        
        return all_embeddings
    
    def _embed_batch_internal(self, texts: List[str]) -> List[List[float]]:
        """内部批量生成方法
        
        Args:
            texts: 输入文本列表（已分批）
            
        Returns:
            Embedding 向量列表
        """
        # 构建请求体
        payload = {
            "input": texts if len(texts) > 1 else texts[0],
            "model": self.model,
        }
        
        # 重试逻辑
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Embedding 请求 (尝试 {attempt + 1}/{self.max_retries + 1}): {len(texts)} 个文本")
                
                # 发送请求
                response = self.session.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                
                # 解析响应
                result = response.json()
                
                # 标准 OpenAI Embedding 响应格式
                if "data" in result:
                    embeddings = [item["embedding"] for item in result["data"]]
                    logger.debug(f"Embedding 成功: {len(embeddings)} 个向量")
                    return embeddings
                else:
                    logger.error(f"未知的 Embedding 响应格式: {result}")
                    raise ValueError(f"未知的响应格式: {result}")
                    
            except requests.exceptions.ProxyError as e:
                last_exception = e
                error_msg = str(e)
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"代理连接失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {error_msg}. "
                        f"{wait_time:.1f}秒后重试..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"代理连接失败，已达到最大重试次数: {error_msg}\n"
                        f"提示：可以尝试以下解决方案：\n"
                        f"1. 检查代理设置是否正确\n"
                        f"2. 设置环境变量 NO_PROXY=1 或 DISABLE_PROXY=1 来禁用代理\n"
                        f"3. 设置环境变量 HTTP_PROXY 和 HTTPS_PROXY 来配置代理\n"
                        f"4. 检查网络连接是否正常"
                    )
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                error_msg = str(e)
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"连接失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {error_msg}. "
                        f"{wait_time:.1f}秒后重试..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"连接失败，已达到最大重试次数: {error_msg}")
            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1}). "
                        f"{wait_time:.1f}秒后重试..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"请求超时，已达到最大重试次数")
            except requests.exceptions.HTTPError as e:
                # HTTP错误（4xx, 5xx）通常不需要重试，除非是5xx服务器错误
                if e.response and e.response.status_code >= 500:
                    last_exception = e
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(
                            f"服务器错误 {e.response.status_code} (尝试 {attempt + 1}/{self.max_retries + 1}). "
                            f"{wait_time:.1f}秒后重试..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"服务器错误，已达到最大重试次数: {e.response.status_code}")
                else:
                    # 4xx错误通常不需要重试
                    raise
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                # JSON解析错误不需要重试
                logger.error(f"Embedding API 响应解析失败: {e}")
                raise
        
        # 如果所有重试都失败，抛出最后一个异常
        if last_exception:
            raise last_exception
    
    def get_embedding_dimension(self) -> int:
        """获取 embedding 维度
        
        Returns:
            Embedding 向量维度
        """
        # text-embedding-ada-002 的维度是 1536
        try:
            test_embedding = self.embed("test")
            return len(test_embedding)
        except Exception as e:
            logger.warning(f"无法获取 embedding 维度: {e}")
            return 1536  # 默认维度
    
    def test_connection(self) -> tuple[bool, str]:
        """测试 API 连接
        
        Returns:
            (是否成功, 消息)
        """
        try:
            embedding = self.embed("测试")
            dim = len(embedding)
            return True, f"连接成功! Embedding 维度: {dim}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
