try:
    from langchain.chains.retrieval import create_retrieval_chain
    print("Import specific success")
except ImportError:
    try:
        from langchain.chains import create_retrieval_chain
        print("Import generic success")
    except ImportError as e:
        print(f"Import failed: {e}")
