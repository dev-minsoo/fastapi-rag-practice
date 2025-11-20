import os
from typing import List
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from openai import OpenAI

class RAGService:
    def __init__(self):
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        # Use a lightweight model for local embedding
        self.model_name = "all-MiniLM-L6-v2"
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=self.model_name)
        
        # Create or get a collection
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_function
        )
        
        # Initialize OpenAI Client (expects OPENAI_API_KEY in env)
        self.openai_client = OpenAI()

    def load_and_chunk(self, file_path: str, chunk_size: int = 1000) -> List[str]:
        """Reads a text file and splits it into chunks."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        if file_path.endswith(".md"):
            return self.chunk_markdown(text, chunk_size)
            
        # Simple chunking by characters for demonstration
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        return chunks

    def chunk_markdown(self, text: str, chunk_size: int) -> List[str]:
        """Splits Markdown text by headers to preserve semantic context."""
        import re
        # Split by headers (capture the header so we can keep it)
        # Matches lines starting with 1-6 # followed by a space
        headers_pattern = r'(^#{1,6}\s.+)'
        splits = re.split(headers_pattern, text, flags=re.MULTILINE)
        
        chunks = []
        current_chunk = ""
        
        for split in splits:
            if not split.strip():
                continue
                
            # If the split is a header (starts with #), start a new chunk
            if re.match(headers_pattern, split, flags=re.MULTILINE):
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = split
            else:
                current_chunk += "\n" + split
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def embed_and_store(self, chunks: List[str]):
        """Embeds chunks and stores them in ChromaDB."""
        if not chunks:
            return
            
        # Generate deterministic IDs based on content hash to avoid duplicates
        import hashlib
        ids = [hashlib.md5(chunk.encode()).hexdigest() for chunk in chunks]
        
        # ChromaDB handles embedding generation automatically if we provide the function
        self.collection.upsert(
            documents=chunks,
            ids=ids
        )

    def query(self, question: str, n_results: int = 3) -> List[dict]:
        """Queries the knowledge base for relevant chunks."""
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )
        
        # results['documents'] is a list of lists (one list per query)
        # results['distances'] is also a list of lists
        if results['documents'] and results['distances']:
            documents = results['documents'][0]
            distances = results['distances'][0]
            
            return [
                {"text": doc, "score": dist}
                for doc, dist in zip(documents, distances)
            ]
        return []

    def get_all_documents(self):
        """Returns all documents in the collection."""
        # get() with no arguments returns all items (up to a limit, usually)
        return self.collection.get(include=["documents"])

    def generate_answer(self, question: str, context_chunks: List[str]) -> str:
        """Generates an answer using OpenAI based on the context."""
        if not context_chunks:
            return "I don't have enough information to answer that."
            
        context = "\n\n".join(context_chunks)
        
        prompt = f"""
        You are a helpful assistant. Answer the question based ONLY on the following context.
        If the answer is not in the context, say "I don't know".
        
        Context:
        {context}
        
        Question:
        {question}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def reset_database(self):
        """Resets the database by deleting and recreating the collection."""
        try:
            self.client.delete_collection("knowledge_base")
        except ValueError:
            # Collection might not exist
            pass
            
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            embedding_function=self.embedding_function
        )

# Singleton instance
rag_service = RAGService()
