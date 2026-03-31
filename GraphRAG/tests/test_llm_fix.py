"""测试修复后的 LLM API"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import settings
from src.api.azure_llm_adapter import AzureLLMAdapter
from loguru import logger

def test_basic_request():
    """测试基本请求（仅model和input字段）"""
    print("=" * 60)
    print("测试 LLM API - 基本请求")
    print("=" * 60)
    
    adapter = AzureLLMAdapter(
        endpoint=settings.llm_endpoint,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )
    
    try:
        print("\n测试简单文本生成...")
        result = adapter.generate("hello")
        print(f"✅ 成功!")
        print(f"响应: {result}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        logger.exception("测试失败")
        return False

if __name__ == "__main__":
    success = test_basic_request()
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！LLM API 工作正常")
    else:
        print("❌ 测试失败，请查看上面的错误信息")
    print("=" * 60)
