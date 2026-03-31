import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from .llm import get_embeddings

VECTOR_STORE_PATH = "./chroma_db"

def get_vector_store():
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=VECTOR_STORE_PATH,
        embedding_function=embeddings,
        collection_name="rag_collection"
    )

async def process_document(file_path: str, filename: str):
    if filename.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif filename.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    else:
        # Default to text loader for others
        loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
    
    docs = loader.load()
    print(f"DEBUG: Loaded {len(docs)} documents from {filename}")
    
    # Add metadata
    for doc in docs:
        doc.metadata["source"] = filename
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(docs)
    print(f"DEBUG: Created {len(splits)} splits")
    
    # Filter out empty content
    splits = [split for split in splits if split.page_content.strip()]
    print(f"DEBUG: {len(splits)} splits remain after filtering empty content")

    if not splits:
        print("DEBUG: No splits to add to vector store.")
        return 0

    vector_store = get_vector_store()
    vector_store.add_documents(documents=splits)
    
    return len(splits)

def retrieve_documents(query: str, k: int = 4):
    vector_store = get_vector_store()
    # Using MMQ (Max Marginal Relevance) for diversity
    return vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k}
    ).invoke(query)
