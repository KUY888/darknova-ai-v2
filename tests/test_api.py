def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"success": True, "data": {"status": "ok"}}


def test_register_and_duplicates(client):
    body = {"username": "carol", "email": "carol@example.com", "password": "password123"}
    r = client.post("/auth/register", json=body)
    assert r.status_code == 201 and "password" not in str(r.json())
    assert client.post("/auth/register", json=body).status_code == 409
    assert client.post("/auth/register", json={**body, "username": "carol2"}).status_code == 409
    assert client.post("/auth/register", json={**body, "username": "x"}).status_code == 422


def test_login(client, auth):
    r = client.post("/auth/login", json={"identifier": "alice", "password": "wrong-pass"})
    assert r.status_code == 401 and r.json()["success"] is False
    assert client.post("/auth/login", json={"identifier": "alice@example.com", "password": "password123"}).status_code == 200


def test_unauthorized(client):
    for path in ("/users/me", "/conversations"):
        r = client.get(path)
        assert r.status_code == 401 and r.json()["success"] is False
    assert client.get("/users/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_logout_revokes_token(client, auth):
    assert client.post("/auth/logout", headers=auth).status_code == 200
    assert client.get("/users/me", headers=auth).status_code == 401


def test_profile_and_update(client, auth, auth2):
    d = client.get("/users/me", headers=auth).json()["data"]
    assert d["username"] == "alice" and d["stats"]["conversations"] == 0
    assert "password_hash" not in d and "password" not in d
    r = client.patch("/users/me", headers=auth, json={"display_name": "Alice", "bio": "hi"})
    assert r.json()["data"]["display_name"] == "Alice"
    assert client.patch("/users/me", headers=auth, json={"username": "bob"}).status_code == 409
    assert client.patch("/users/me", headers=auth, json={"bio": "x" * 301}).status_code == 422


def test_avatar(client, auth):
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 50
    r = client.post("/users/me/avatar", headers=auth, files={"file": ("a.png", png, "image/png")})
    assert r.status_code == 200 and r.json()["data"]["avatar_url"]
    assert client.post("/users/me/avatar", headers=auth, files={"file": ("a.txt", b"hi", "text/plain")}).status_code == 400
    assert client.post("/users/me/avatar", headers=auth, files={"file": ("a.png", b"notpng", "image/png")}).status_code == 400
    assert client.delete("/users/me/avatar", headers=auth).json()["data"]["avatar_url"] is None


def test_public_profile(client, auth):
    d = client.get("/users/alice").json()["data"]
    assert set(d) == {"username", "display_name", "bio", "avatar_url", "created_at"}
    assert client.get("/users/nobody").status_code == 404


def test_conversation_crud_and_search(client, auth):
    c = client.post("/conversations", headers=auth, json={"title": "Plan", "mode": "PLAN"}).json()["data"]
    cid = c["id"]
    assert client.patch(f"/conversations/{cid}", headers=auth, json={"title": "Renamed"}).json()["data"]["title"] == "Renamed"
    assert len(client.get("/conversations?q=renam", headers=auth).json()["data"]) == 1
    assert client.get("/conversations?q=zzz", headers=auth).json()["data"] == []
    assert client.post("/conversations", headers=auth, json={"mode": "BAD"}).status_code == 422
    assert client.delete(f"/conversations/{cid}", headers=auth).status_code == 200
    assert client.get(f"/conversations/{cid}", headers=auth).status_code == 404


def test_conversation_ownership(client, auth, auth2):
    cid = client.post("/conversations", headers=auth, json={}).json()["data"]["id"]
    for method, url, kw in (("get", f"/conversations/{cid}", {}), ("patch", f"/conversations/{cid}", {"json": {"title": "x"}}),
                            ("delete", f"/conversations/{cid}", {}), ("get", f"/conversations/{cid}/messages", {}),
                            ("post", f"/conversations/{cid}/messages", {"json": {"content": "hi"}})):
        assert getattr(client, method)(url, headers=auth2, **kw).status_code == 404
    assert client.post("/chat", headers=auth2, json={"message": "hi", "conversation_id": cid}).status_code == 404


def test_chat(client, auth):
    r = client.post("/chat", headers=auth, json={"message": "ping", "mode": "CODE"})
    d = r.json()["data"]
    assert r.status_code == 200 and d["reply"]["content"] == "pong" and d["conversation"]["mode"] == "CODE"
    cid = d["conversation"]["id"]
    client.post(f"/conversations/{cid}/messages", headers=auth, json={"content": "again"})
    msgs = client.get(f"/conversations/{cid}/messages", headers=auth).json()["data"]
    assert [m["role"] for m in msgs] == ["user", "assistant", "user", "assistant"]
    assert client.get("/users/me", headers=auth).json()["data"]["stats"]["messages"] == 4
    assert client.post("/chat", headers=auth, json={"message": ""}).status_code == 422


def test_chat_provider_failure(client, auth, monkeypatch):
    from app.providers import ProviderError
    from app.services import ai_service

    class Bad:
        def is_configured(self):
            return True

        def chat(self, m):
            raise ProviderError("boom")

    monkeypatch.setattr(ai_service, "get_provider", lambda: Bad())
    r = client.post("/chat", headers=auth, json={"message": "hi"})
    assert r.status_code == 502 and r.json()["success"] is False and "boom" not in r.text


def test_error_format_404(client):
    r = client.get("/nope")
    assert r.status_code == 404 and r.json()["success"] is False


def test_system(client):
    s = client.get("/system/status").json()["data"]
    assert s["api"] == "online" and s["database"] == "online" and s["ai"] in ("online", "offline")
    a = client.get("/system/about").json()["data"]
    assert a["developer"] == "KUY888 (คุณลีโอ)" and a["version"] == "V2" and a["discord"].startswith("https://discord.gg/")
    assert "api_key" not in str(a).lower()
    assert client.get("/app-profile").status_code == 200 and client.get("/static/logo.jpg").status_code == 200
