from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
from backend.app.services.vector_store_pinecone import get_pinecone_vectorstore

def load_knowledge_base(file_path: str):
    """Loads FAQ documents and stores them in Pinecone."""
    loader = TextLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(docs)

    # ✅ Load into Pinecone
    vectorstore = get_pinecone_vectorstore()
    vectorstore.add_documents(split_docs)

    print("✅ Knowledge Base Loaded Successfully.")

# Run this script to upload documents
if __name__ == "__main__":
    load_knowledge_base("data/support_faqs.txt")