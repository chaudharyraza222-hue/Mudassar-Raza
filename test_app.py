import pytest
from fastapi.testclient import TestClient
from app import app
import os
import time

client = TestClient(app)

def unique_email(prefix="test"):
    return f"{prefix}_{int(time.time() * 1000)}@example.com"

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_register_and_login():
    email = unique_email("register")
    password = "password123"
    
    # Register
    r = client.post("/api/register", json={"name": "Test User", "email": email, "password": password})
    assert r.status_code == 200
    assert "message" in r.json()
    
    # Login
    r = client.post("/api/login", json={"email": email, "password": password})
    assert r.status_code == 200
    assert "token" in r.json()
    return r.json()["token"]

def test_profile():
    # Register and login first
    email = unique_email("profile")
    password = "password123"
    client.post("/api/register", json={"name": "Test User", "email": email, "password": password})
    r = client.post("/api/login", json={"email": email, "password": password})
    token = r.json()["token"]
    
    # Get profile
    r = client.get("/api/profile", params={"token": token})
    assert r.status_code == 200
    assert r.json()["email"] == email

def test_sourcing_fetch():
    # Test fetching from a source link (mock mode)
    r = client.post("/api/sourcing/products/fetch", json={
        "source_link": "http://127.0.0.1:8000/static/source-pages/kh-204.html",
        "product_name": "Test Product",
        "brand": "Test Brand",
        "sku": "TEST-001"
    })
    assert r.status_code == 200
    data = r.json()
    assert "title" in data
    assert "success" in data

def test_import_template():
    r = client.get("/api/sourcing/import/template")
    assert r.status_code == 200
    # Should return either xlsx or csv
    assert "spreadsheetml" in r.headers.get("content-type", "") or "csv" in r.headers.get("content-type", "")

def test_ebay_fetch_start():
    r = client.post("/api/sourcing/ebay/fetch-seller", json={"seller_link": "testuser"})
    assert r.status_code == 200
    assert r.json()["status"] == "started"

def test_repricer():
    r = client.get("/api/repricer/products")
    assert r.status_code == 200
    assert "products" in r.json()

def test_amazon_credentials_status():
    r = client.get("/api/amazon/credentials/status")
    assert r.status_code == 200
    assert "configured" in r.json()
    assert "setup_steps" in r.json()

def test_amazon_orders():
    r = client.get("/api/amazon/orders")
    assert r.status_code == 200
    assert "orders" in r.json()
    assert "total" in r.json()

def test_amazon_orders_stats():
    r = client.get("/api/amazon/orders/stats")
    assert r.status_code == 200
    assert "total_orders" in r.json()

def test_amazon_orders_sync():
    # Returns 400 when no credentials configured (expected in test env)
    r = client.post("/api/amazon/orders/sync")
    assert r.status_code in (200, 400)
    data = r.json()
    if r.status_code == 200:
        assert "synced" in data
        assert "updated" in data

def test_ai_text_generate():
    r = client.post("/api/ai/text/generate", json={
        "product_name": "Test Product",
        "brand": "Test Brand",
        "category": "Home & Kitchen"
    })
    assert r.status_code == 200
    assert "title" in r.json()
    assert "bullet_points" in r.json()

def test_ai_image_generate():
    r = client.post("/api/ai/image/generate", json={
        "product_id": "TEST-001",
        "product_name": "Test Product",
        "mode": "creative",
        "fidelity": 80,
        "standing_instructions": "white background",
        "concept_mode": "suggest",
        "image_slot": "Main"
    })
    assert r.status_code == 200
    assert "images" in r.json()
    assert len(r.json()["images"]) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])