import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

load_dotenv()

def get_llm():
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )

def get_embeddings():
    return AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME"),
        api_version=os.getenv("AZURE_EMBEDDING_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_EMBEDDING_ENDPOINT"),
        api_key=os.getenv("AZURE_EMBEDDING_API_KEY"),
    )
