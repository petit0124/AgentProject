import os
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from ingestion import get_vector_store
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY")
    )

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_rag_chain():
    llm = get_llm()
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    template = """You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, say that you don't know. 
Use three sentences maximum and keep the answer concise.

Context: {context}

Question: {input}

Answer:"""

    prompt = ChatPromptTemplate.from_template(template)

    rag_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain, retriever

# Simple in-memory history management for demo purposes
# In a real app, use a database or session-based storage
chat_history_storage = []

def add_to_history(user_input, answer, contexts):
    chat_history_storage.append({
        "user_input": user_input,
        "answer": answer,
        "contexts": [doc.page_content for doc in contexts]
    })

def get_chat_history():
    return chat_history_storage
