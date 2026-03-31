
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set Azure variables manually for testing if not in .env (or to override)
# User provided values:
# os.environ["AZURE_OPENAI_API_KEY"] = "7215c7fa8f0f4a4eb56ad02f066cc7a6"
# os.environ["AZURE_OPENAI_ENDPOINT"] = "https://fxiaoke-azureopenai-02.openai.azure.com"
# os.environ["AZURE_OPENAI_API_VERSION"] = "2025-04-01-preview"
# os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "azure02-gpt-5"

from llm_clients import get_llm_client
from langchain_core.messages import HumanMessage

def test_azure_connection():
    print("Testing Azure OpenAI Connection...")
    
    try:
        # Initialize client
        # We can pass model_name explicitly or rely on default in MODEL_CONFIGS["azure"]
        client = get_llm_client(provider="azure", model_name="azure02-gpt-5")
        
        # Create a simple message
        messages = [HumanMessage(content="Hello, are you working?")]
        
        # Invoke
        print("Sending request...")
        response = client.invoke(messages)
        
        print("\nResponse received:")
        print(f"Content: {response.content}")
        print("\nSUCCESS: Azure OpenAI connection established and working.")
        
    except Exception as e:
        print(f"\nERROR: Failed to connect or get response from Azure OpenAI.")
        print(f"Details: {str(e)}")

if __name__ == "__main__":
    test_azure_connection()
