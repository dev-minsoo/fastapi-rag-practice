from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List
import os

from app.services.rag_service import rag_service

router = APIRouter(prefix="/rag", tags=["rag"])

class SearchResult(BaseModel):
    text: str
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    answer: str

@router.post("/index")
async def index_knowledge_base():
    """
    Triggers the loading and indexing of the knowledge base.
    Scans all .txt and .md files in the data/ directory.
    """
    try:
        data_dir = "data"
        if not os.path.exists(data_dir):
             raise HTTPException(status_code=404, detail="Data directory not found.")

        total_chunks = 0
        indexed_files = []

        for filename in os.listdir(data_dir):
            if filename.endswith(".txt") or filename.endswith(".md"):
                file_path = os.path.join(data_dir, filename)
                chunks = rag_service.load_and_chunk(file_path)
                rag_service.embed_and_store(chunks)
                total_chunks += len(chunks)
                indexed_files.append(filename)
        
        return {
            "message": f"Successfully indexed {total_chunks} chunks from {len(indexed_files)} files.",
            "files": indexed_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SearchResponse)
async def search_knowledge_base(q: str = Query(..., description="The search query")):
    """
    Searches the knowledge base for relevant information and generates an answer.
    """
    try:
        results = rag_service.query(q)
        # Extract just the text for the LLM context
        context_chunks = [r["text"] for r in results]
        answer = rag_service.generate_answer(q, context_chunks)
        return {"results": results, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset_knowledge_base():
    """
    Resets the knowledge base by deleting all data.
    """
    try:
        rag_service.reset_database()
        return {"message": "Knowledge base reset successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inspect")
async def inspect_knowledge_base():
    """
    Returns all documents stored in the knowledge base.
    """
    try:
        return rag_service.get_all_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
