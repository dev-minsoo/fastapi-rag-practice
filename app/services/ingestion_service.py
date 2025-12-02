from app.services.crawler import WebCrawler
from app.services.rag_service import rag_service
from starlette.concurrency import run_in_threadpool
from typing import List

class IngestionService:
    def __init__(self):
        self.crawler = WebCrawler()
        self.rag_service = rag_service

    async def ingest_url(self, url: str) -> bool:
        """Crawls a URL and indexes the content."""
        text = await run_in_threadpool(self.crawler.crawl, url)
        if not text:
            return False
            
        # Delete existing documents for this source
        # Accessing collection directly from rag_service might be a bit leaky, 
        # but for now it's the quickest way without adding delete method to RAGService interface explicitly for this.
        # Ideally RAGService should expose a delete_by_source method.
        await run_in_threadpool(self.rag_service.collection.delete, where={"source": url})
            
        # Chunk the text (simple chunking for now, could be smarter for HTML)
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        
        # Create metadata for each chunk
        metadatas = [{"source": url} for _ in chunks]
        
        await self.rag_service.embed_and_store(chunks, metadatas)
        return True

    async def ingest_sitemap(self, sitemap_url: str, filter_pattern: str = None) -> int:
        """Ingests all URLs from a sitemap, optionally filtering by a pattern."""
        urls = await run_in_threadpool(self.crawler.get_sitemap_urls, sitemap_url)
        
        if filter_pattern:
            urls = [url for url in urls if filter_pattern in url]
            
        count = 0
        for url in urls:
            if await self.ingest_url(url):
                count += 1
        return count

ingestion_service = IngestionService()
