# ..._test.py
from fastapi.testclient import TestClient

from scripts.session_3.api import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, FastAPI!"}
