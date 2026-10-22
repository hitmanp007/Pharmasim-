import sqlite3
from app import create_app
from conftest import token


def test_health_and_pages(client):
    assert client.get("/health").json == {"status": "ok"}
    for u in ("/", "/m/clinical", "/m/qc", "/progress", "/about", "/m/qc/weight-variation"):
        assert client.get(u).status_code == 200


def test_invalid_ids_404(client):
    assert client.get("/m/other").status_code == 404
    assert client.get("/m/qc/nope").status_code == 404


def test_answers_not_exposed(client):
    html = client.get("/m/clinical/allergy-amoxicillin").get_data(as_text=True)
    assert "Correct. Resolve" not in html and "points" not in html


def test_post_requires_csrf(client):
    assert client.post("/m/qc/weight-variation", data={"mean": "200"}).status_code == 400


def test_qc_submit_scores_and_records(client):
    t = token(client)
    r = client.post("/m/qc/weight-variation", data={"csrf_token": t, "mean": "200", "decision": "pass"})
    assert r.status_code == 200 and "6 / 6" in r.get_data(as_text=True)
    assert "weight-variation" in client.get("/progress").get_data(as_text=True)


def test_missing_and_bad_input_400(client):
    t = token(client)
    assert client.post("/m/qc/weight-variation", data={"csrf_token": t}).status_code == 400
    assert client.post("/m/qc/weight-variation", data={"csrf_token": t, "mean": "abc", "decision": "pass"}).status_code == 400


def test_history_isolated_between_sessions(app):
    a, b = app.test_client(), app.test_client()
    a.post("/m/clinical/allergy-amoxicillin", data={"csrf_token": token(a), "q1": "b", "q2": ["a", "b"]})
    assert "allergy-amoxicillin" in a.get("/progress").get_data(as_text=True)
    assert "allergy-amoxicillin" not in b.get("/progress").get_data(as_text=True)


def test_db_initialised(app):
    con = sqlite3.connect(app.config["DATABASE"])
    assert con.execute("SELECT name FROM sqlite_master WHERE name='attempts'").fetchone()


def test_production_requires_secret(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("PHARMASIM_ENV", "production")
    try:
        create_app({"DATABASE": ":memory:"})
        assert False
    except RuntimeError:
        pass
