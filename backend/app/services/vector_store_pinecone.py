import os
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore 
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# ✅ Load API Keys from environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "support-knowledge-base"

# ✅ Initialize Pinecone Client (Correct way)
pc = Pinecone(api_key=PINECONE_API_KEY)

# ✅ Check if Index Exists and Create if Necessary
def create_pinecone_index():
    """Creates a Pinecone index for storing knowledge documents."""
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME, 
            dimension=1536, 
            spec=ServerlessSpec(cloud="gcp", region="europe-west4"),
            metric="cosine"  # You can also use 'dotproduct' or 'euclidean'
        )

def upload_documents():
    """Upload support articles to Pinecone."""
    create_pinecone_index()
    
    embeddings = OpenAIEmbeddings()
    vectorstore = PineconeVectorStore(index=pc.Index(INDEX_NAME), embedding=embeddings)
    
    # Example knowledge base documents
    documents = [
        {"text": "To reset your password, click 'Forgot Password' on the login page and follow the instructions.", "metadata": {"category": "password_reset"}},
        {"text": "Refunds are processed within 5-7 business days. Contact support if you don’t receive it.", "metadata": {"category": "billing"}},
        {"text": "If you’re experiencing login issues, try clearing your cache and cookies.", "metadata": {"category": "technical"}}
    ]
    
    # Insert documents into Pinecone
    for doc in documents:
        vectorstore.add_texts([doc["text"]], metadatas=[doc["metadata"]])

    print("✅ Documents successfully uploaded to Pinecone!")

def get_pinecone_vectorstore():
    """Loads the Pinecone vector database."""
    create_pinecone_index()  # Ensure index exists
    embeddings = OpenAIEmbeddings()
    index = pc.Index(INDEX_NAME)  # Get reference to the Pinecone index

    return PineconeVectorStore(index=index, embedding=embeddings)

if __name__ == "__main__":
    upload_documents()