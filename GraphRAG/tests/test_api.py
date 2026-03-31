"""API 连接测试工具"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.api.azure_llm_adapter import AzureLLMAdapter
from src.api.azure_embedding_adapter import AzureEmbeddingAdapter
from loguru import logger


def test_llm_api():
    """测试 LLM API"""
    print("=" * 60)
    print("测试 LLM API")
    print("=" * 60)
    
    try:
        adapter = AzureLLMAdapter(
            endpoint=settings.llm_endpoint,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
        
        # 测试基本生成
        print("\n测试 1: 基本文本生成")
        result = adapter.generate("你好，请介绍一下你自己", max_tokens=50)
        print(f"✅ 成功!\n响应: {result}\n")
        
        # 测试对话生成
        print("测试 2: 对话生成")
        messages = [
            {"role": "system", "content": "你是一个有帮助的助手"},
            {"role": "user", "content": "什么是知识图谱？"},
        ]
        result = adapter.generate_chat(messages, max_tokens=100)
        print(f"✅ 成功!\n响应: {result}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        logger.exception("LLM API 测试失败")
        return False


def test_embedding_api():
    """测试 Embedding API"""
    print("=" * 60)
    print("测试 Embedding API")
    print("=" * 60)
    
    try:
        adapter = AzureEmbeddingAdapter(
            endpoint=settings.embedding_endpoint,
            api_key=settings.embedding_api_key,
            model=settings.embedding_model,
        )
        
        # 测试单个文本
        print("\n测试 1: 单个文本 Embedding")
        text = "这是一个测试文本"
        embedding = adapter.embed(text)
        print(f"✅ 成功!")
        print(f"Embedding 维度: {len(embedding)}")
        print(f"前 5 个值: {embedding[:5]}\n")
        
        # 测试批量
        print("测试 2: 批量 Embedding")
        texts = ["文本1", "文本2", "文本3"]
        embeddings = adapter.embed_batch(texts)
        print(f"✅ 成功!")
        print(f"生成了 {len(embeddings)} 个 embeddings")
        print(f"每个维度: {len(embeddings[0])}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        logger.exception("Embedding API 测试失败")
        return False


def main():
    """主函数"""
    print("\n🔧 GraphRAG API 连接测试工具\n")
    
    # 检查配置
    is_valid, error_msg = settings.validate()
    if not is_valid:
        print(f"❌ 配置错误: {error_msg}")
        print("请检查 .env 文件配置")
        return
    
    print("✅ 配置验证通过\n")
    
    # 测试 LLM
    llm_ok = test_llm_api()
    
    # 测试 Embedding
    emb_ok = test_embedding_api()
    
    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"LLM API: {'✅ 通过' if llm_ok else '❌ 失败'}")
    print(f"Embedding API: {'✅ 通过' if emb_ok else '❌ 失败'}")
    print()
    
    if llm_ok and emb_ok:
        print("🎉 所有测试通过! 可以开始使用 GraphRAG 了。")
    else:
        print("⚠️ 部分测试失败，请检查配置和网络连接。")


if __name__ == "__main__":
    main()
