"""
LLM配置模块
配置Azure OpenAI连接
"""
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

# 加载环境变量
load_dotenv()


def get_llm(temperature=0.7, streaming=False):
    """
    获取配置好的Azure OpenAI LLM实例
    
    Args:
        temperature: 温度参数，控制输出随机性
        streaming: 是否启用流式输出
    
    Returns:
        AzureChatOpenAI实例
    """
    # 从endpoint中提取base_url和deployment_name
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    # 解析endpoint获取base_url
    # endpoint格式: https://xxx.openai.azure.com/openai/deployments/DEPLOYMENT_NAME/chat/completions?api-version=xxx
    if "/openai/deployments/" in endpoint:
        base_url = endpoint.split("/openai/deployments/")[0]
        deployment_part = endpoint.split("/openai/deployments/")[1]
        deployment_name = deployment_part.split("/")[0]
        api_version = endpoint.split("api-version=")[1] if "api-version=" in endpoint else "2023-07-01-preview"
    else:
        raise ValueError("Invalid AZURE_OPENAI_ENDPOINT format")
    
    return AzureChatOpenAI(
        azure_endpoint=base_url,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version=api_version,
        temperature=temperature,
        streaming=streaming,
    )


# 创建默认LLM实例
llm = get_llm()
