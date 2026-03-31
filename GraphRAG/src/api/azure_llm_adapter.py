"""Azure OpenAI LLM 适配器 - 适配非标准的 /openai/responses endpoint"""
import json
import time
import os
import requests
from typing import Any, Dict, List, Optional, Iterator
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class AzureLLMAdapter:
    """Azure OpenAI LLM 适配器
    
    适配非标准的 Azure OpenAI endpoint: /openai/responses
    使用 Bearer token 认证
    """
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: int = 120,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        proxy: Optional[str] = None,
    ):
        """初始化 LLM 适配器
        
        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: API key (用于 Bearer token)
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒），会指数递增
            proxy: 代理服务器地址（格式：http://host:port），None表示使用系统代理或禁用
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 设置请求头
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
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
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """生成文本
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数（覆盖默认值）
            max_tokens: 最大 token 数（覆盖默认值）
            
        Returns:
            生成的文本
        """
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # 构建请求体
        # 注意：此API可能不支持temperature和max_tokens参数，仅发送必需字段
        payload = {
            "model": self.model,
            "input": messages,
        }
        
        # 可选：如果API支持这些参数，可以取消注释
        # if temperature is not None:
        #     payload["temperature"] = temperature
        # elif self.temperature is not None and self.temperature != 0.0:
        #     payload["temperature"] = self.temperature
        #     
        # if max_tokens is not None:
        #     payload["max_tokens"] = max_tokens
        # elif self.max_tokens is not None:
        #     payload["max_tokens"] = self.max_tokens
        
        # 重试逻辑
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"LLM 请求 (尝试 {attempt + 1}/{self.max_retries + 1}): {json.dumps(payload, ensure_ascii=False)[:200]}...")
                
                # 发送请求
                response = self.session.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                break  # 成功则跳出重试循环
                
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
        
        # 如果所有重试都失败，抛出最后一个异常
        if last_exception:
            raise last_exception
        
        try:
            
            # 解析响应
            result = response.json()
            logger.debug(f"LLM 响应: {json.dumps(result, ensure_ascii=False)[:200]}...")
            
            # 尝试不同的响应格式
            # 标准 OpenAI 格式
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            # output 字段 - 可能是复杂结构
            elif "output" in result:
                output = result["output"]
                # 如果output是列表，遍历查找text
                if isinstance(output, list):
                    for item in output:
                        if isinstance(item, dict):
                            # 查找content字段
                            if "content" in item:
                                content = item["content"]
                                # content可能也是列表
                                if isinstance(content, list):
                                    for c in content:
                                        if isinstance(c, dict) and "text" in c:
                                            return c["text"]
                                elif isinstance(content, str):
                                    return content
                            # 直接查找text字段
                            elif "text" in item:
                                return item["text"]
                # 如果output是字符串
                elif isinstance(output, str):
                    return output
                # 如果output是字典
                elif isinstance(output, dict) and "content" in output:
                    return output["content"]
            # response 字段
            elif "response" in result:
                return result["response"]
            # text 字段
            elif "text" in result:
                return result["text"]
            else:
                logger.error(f"未知的响应格式: {result}")
                raise ValueError(f"未知的响应格式，可用字段: {list(result.keys())}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API 请求失败: {e}")
            # 尝试获取响应内容以便调试
            try:
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"响应状态码: {e.response.status_code}")
                    logger.error(f"响应内容: {e.response.text}")
            except:
                pass
            raise
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"LLM API 响应解析失败: {e}")
            raise
    
    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """生成对话文本
        
        Args:
            messages: 对话消息列表，格式: [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
            
        Returns:
            生成的文本
        """
        # 构建请求体
        # 注意：此API可能不支持temperature和max_tokens参数，仅发送必需字段
        payload = {
            "model": self.model,
            "input": messages,
        }
        
        # 可选：如果API支持这些参数，可以取消注释
        # if temperature is not None:
        #     payload["temperature"] = temperature
        # elif self.temperature is not None and self.temperature != 0.0:
        #     payload["temperature"] = self.temperature
        #     
        # if max_tokens is not None:
        #     payload["max_tokens"] = max_tokens
        # elif self.max_tokens is not None:
        #     payload["max_tokens"] = self.max_tokens
        
        # 重试逻辑
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"LLM Chat 请求 (尝试 {attempt + 1}/{self.max_retries + 1}): {json.dumps(payload, ensure_ascii=False)[:200]}...")
                
                response = self.session.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                break  # 成功则跳出重试循环
                
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
        
        # 如果所有重试都失败，抛出最后一个异常
        if last_exception:
            raise last_exception
        
        try:
            
            result = response.json()
            logger.debug(f"LLM Chat 响应: {json.dumps(result, ensure_ascii=False)[:200]}...")
            
            # 解析响应
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            elif "output" in result:
                return result["output"]
            elif "response" in result:
                return result["response"]
            elif "text" in result:
                return result["text"]
            else:
                raise ValueError(f"未知的响应格式: {result}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM Chat API 请求失败: {e}")
            # 尝试获取响应内容以便调试
            try:
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"响应状态码: {e.response.status_code}")
                    logger.error(f"响应内容: {e.response.text}")
            except:
                pass
            raise
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"LLM Chat API 响应解析失败: {e}")
            raise
    
    def test_connection(self) -> tuple[bool, str]:
        """测试 API 连接
        
        Returns:
            (是否成功, 消息)
        """
        try:
            result = self.generate("Hello", max_tokens=10)
            return True, f"连接成功! 响应: {result[:50]}..."
        except Exception as e:
            return False, f"连接失败: {str(e)}"
