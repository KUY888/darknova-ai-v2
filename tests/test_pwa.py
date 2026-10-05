import json


def test_manifest(client):
    r = client.get("/manifest.webmanifest")
    assert r.status_code == 200 and "manifest+json" in r.headers["content-type"]
    m = json.loads(r.text)
    assert m["display"] == "standalone" and m["start_url"] == "/" and m["name"]
    sizes = {(i["sizes"], i["purpose"]) for i in m["icons"]}
    assert ("192x192", "any") in sizes and ("512x512", "any") in sizes and ("512x512", "maskable") in sizes
    for i in m["icons"]:
        ic = client.get(i["src"])
        assert ic.status_code == 200 and ic.headers["content-type"] == "image/png"


def test_service_worker(client):
    r = client.get("/sw.js")
    assert r.status_code == 200 and "javascript" in r.headers["content-type"]
    assert r.headers["cache-control"] == "no-cache"
    assert all(p in r.text for p in ("'/auth'", "'/chat'", "'/users'", "'/conversations'"))


def test_index_has_pwa_tags_and_backend_intact(client, auth):
    html = client.get("/").text
    for needle in ('rel="manifest"', 'name="theme-color"', "apple-touch-icon", "serviceWorker"):
        assert needle in html
    assert client.get("/health").status_code == 200
    assert client.post("/chat", headers=auth, json={"message": "hi"}).status_code == 200
