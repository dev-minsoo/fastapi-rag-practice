from pydantic import BaseModel
from typing import List, Optional

class UrlRequest(BaseModel):
    url: str

class SitemapRequest(BaseModel):
    sitemap_url: str
    filter_pattern: Optional[str] = None

class SearchResult(BaseModel):
    text: str
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    answer: str
