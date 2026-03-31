import sys
import os
import traceback
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load environment variables from backend/.env
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

print("Current working directory:", os.getcwd())
print("Attempting to reproduce RAG error...")

try:
    import rag
    print("Imported rag module.")
    
    print("Initializing RAG chain...")
    chain, retriever = rag.get_rag_chain()
    print("RAG chain initialized.")
    
    query = "test query"
    print(f"Invoking chain with query: '{query}'")
    
    # Try different invocation methods if one fails or just the standard one
    # The code uses: answer = chain.invoke(request.message)
    response = chain.invoke(query)
    print("Chain invocation successful!")
    print("Response:", response)

except Exception as e:
    print("\n!!! ERROR CAUGHT !!!")
    traceback.print_exc()
    sys.exit(1)
