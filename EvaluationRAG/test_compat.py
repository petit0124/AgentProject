import sys
print(sys.executable)
try:
    import langchain
    print(f"LangChain: {langchain.__version__}")
    from langchain.chains import create_retrieval_chain
    print("SUCCESS: create_retrieval_chain")
except ImportError as e:
    print(f"FAIL: {e}")
