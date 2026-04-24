from app.main import app


def test_get_missing_key_returns_404() -> None:
    client = app.test_client()
    response = client.get("/kv/missing")
    assert response.status_code == 404
