import pytest
from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "SECRET_KEY": "test", "SESSION_COOKIE_SECURE": False,
                       "DATABASE": str(tmp_path / "t.db")})


@pytest.fixture
def client(app):
    return app.test_client()


def token(client, url="/"):
    client.get(url)
    with client.session_transaction() as s:
        return s["csrf"]
