try:
    from langchain.chains import create_retrieval_chain
    print("SUCCESS: create_retrieval_chain imported")
except ImportError as e:
    print(f"FAILURE: {e}")
    import langchain
    print(f"Langchain file: {langchain.__file__}")
