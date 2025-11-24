from fastapi.testclient import TestClient
from app.main import app
from app.services.rag_service import rag_service
import os

client = TestClient(app)

def test_rag_flow():
    # 1. Ensure the knowledge file exists
    assert os.path.exists("data/claude_code_changelog.md")

    # 2. Index the data
    response = client.post("/rag/index")
    assert response.status_code == 200
    assert "Successfully indexed" in response.json()["message"]

    # 3. Search for something relevant
    response = client.get("/rag/search?q=Claude")
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) > 0
    # Check if at least one result contains "Claude"
    assert any("Claude" in r["text"] for r in results)

    # 4. Search for something else
    response = client.get("/rag/search?q=version")
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) > 0
    assert any("version" in r["text"] for r in results)
