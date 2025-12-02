import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.rag_service import rag_service
from app.services.crawler import WebCrawler

client = TestClient(app)

@pytest.fixture
def mock_crawler():
    # Patch WebCrawler in ingestion_service, not rag_service
    with patch("app.services.ingestion_service.WebCrawler") as MockCrawler:
        instance = MockCrawler.return_value
        instance.crawl.return_value = "Mocked web content for testing."
        
        # We need to patch the instance on the ingestion_service singleton
        from app.services.ingestion_service import ingestion_service
        original_crawler = ingestion_service.crawler
        ingestion_service.crawler = instance
        yield instance
        ingestion_service.crawler = original_crawler

def test_ingest_url(mock_crawler):
    response = client.post("/ingest/url", json={"url": "http://example.com"})
    assert response.status_code == 200
    assert "Successfully ingested" in response.json()["message"]
    mock_crawler.crawl.assert_called_with("http://example.com")

def test_ingest_sitemap(mock_crawler):
    # We want to test the XML parsing logic in get_sitemap_urls, so we need a real WebCrawler instance
    # but we want to mock the network calls.
    from app.services.crawler import WebCrawler
    from app.services.ingestion_service import ingestion_service
    
    real_crawler = WebCrawler()
    
    # Temporarily replace the crawler in the service with our real (but partially mocked) one
    # The fixture will restore the original mock after the test, but we should be careful.
    # Actually, the fixture restores 'original_crawler' which was there BEFORE the fixture ran.
    # If we overwrite ingestion_service.crawler here, the fixture teardown might overwrite it back to original.
    # But we are inside the fixture scope.
    # Let's just overwrite it and let fixture teardown handle restoration? 
    # No, fixture teardown restores what it saved. If we change it here, fixture teardown will restore the ORIGINAL.
    # So our change is temporary for this test function scope if we don't mess up global state.
    # But ingestion_service is global.
    # We should manually restore it or rely on fixture?
    # The fixture restores `ingestion_service.crawler = original_crawler`.
    # So whatever we do here will be overwritten by fixture teardown. That's fine.
    
    ingestion_service.crawler = real_crawler

    # Mock requests.get to return XML content
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.content = b"""
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>http://example.com/page1</loc>
            </url>
            <url>
                <loc>http://example.com/page2</loc>
            </url>
        </urlset>
        """
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # We also need to mock crawl() because ingest_sitemap calls it
        with patch.object(real_crawler, 'crawl', return_value="Mocked content"):
            response = client.post("/ingest/sitemap", json={"sitemap_url": "http://example.com/sitemap.xml"})
            assert response.status_code == 200
            assert "Successfully ingested 2 URLs" in response.json()["message"]

def test_ingest_sitemap_with_filter(mock_crawler):
    # Mock sitemap URLs
    # The mock_crawler fixture mocks the CLASS instantiation.
    # So ingestion_service.crawler is a Mock object.
    # We can set return_value on its methods.
    
    mock_crawler.get_sitemap_urls.return_value = [
        "http://example.com/docs/en/page1",
        "http://example.com/docs/ko/page1",
        "http://example.com/docs/fr/page1"
    ]
    
    response = client.post("/ingest/sitemap", json={
        "sitemap_url": "http://example.com/sitemap.xml",
        "filter_pattern": "/docs/en/"
    })
    assert response.status_code == 200
    assert "Successfully ingested 1 URLs" in response.json()["message"]
    
    # Verify crawl was called only for the filtered URL
    mock_crawler.crawl.assert_called_with("http://example.com/docs/en/page1")
    
    with pytest.raises(AssertionError):
        mock_crawler.crawl.assert_called_with("http://example.com/docs/ko/page1")

def test_search_after_ingestion(mock_crawler):
    # Ingest data
    client.post("/ingest/url", json={"url": "http://example.com"})
    
    # Search for it
    response = client.get("/rag/search?q=Mocked")
    assert response.status_code == 200
    results = response.json()["results"]
    # We can't guarantee the mocked data is returned because we didn't mock the vector store fully in this integration test,
    # but we can check if the request was successful.
    # To be more rigorous, we could mock the embedding/querying too, but this verifies the API wiring.
    assert isinstance(results, list)
