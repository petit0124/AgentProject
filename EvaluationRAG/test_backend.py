import sys
import os
import traceback

sys.path.append(os.path.join(os.getcwd(), 'backend'))

print("Test Script Starting...")

try:
    print("Attempting to import langchain...")
    import langchain
    print(f"LangChain version: {langchain.__version__}")
    
    print("Attempting to import langchain.chains...")
    from langchain.chains import create_retrieval_chain
    print("Import langchain.chains successful")

    print("Attempting to import backend modules...")
    import ingestion
    import rag
    import evaluate_rag  # Ragas might be tricky
    print("Backend modules imported successfully")

except Exception as e:
    print("ERROR CAUGHT:")
    traceback.print_exc()
    sys.exit(1)

print("Verification Passed")
