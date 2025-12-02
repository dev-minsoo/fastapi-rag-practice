from fastapi import APIRouter
from app.schemas import UrlRequest, SitemapRequest
from app.services.ingestion_service import ingestion_service

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/url")
async def ingest_url(request: UrlRequest):
    success = await ingestion_service.ingest_url(request.url)
    if success:
        return {"message": f"Successfully ingested {request.url}"}
    else:
        return {"message": f"Failed to ingest {request.url}", "status": "error"}

@router.post("/sitemap")
async def ingest_sitemap(request: SitemapRequest):
    count = await ingestion_service.ingest_sitemap(request.sitemap_url, request.filter_pattern)
    return {"message": f"Successfully ingested {count} URLs from {request.sitemap_url}"}
