import pytest

def test_create_and_get_channel(client):
    channel_data = {
        "id": "api-test",
        "name": "API Test Channel",
        "enabled": True,
        "source": {"type": "http", "path": "/api", "method": "POST"},
        "destinations": [{"type": "http", "url": "http://api", "method": "POST"}]
    }
    # 创建
    response = client.post("/channels/", json=channel_data)
    assert response.status_code == 201
    # 查询
    response = client.get("/channels/api-test")
    assert response.status_code == 200
    assert response.json()["name"] == "API Test Channel"

def test_get_all_channels(client):
    response = client.get("/channels/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_process_message_for_channel(client):
    # 先确保有一个channel
    channel_data = {
        "id": "process-test",
        "name": "Process Test",
        "enabled": True,
        "source": {"type": "http", "path": "/proc", "method": "POST"},
        "destinations": [{"type": "http", "url": "http://proc", "method": "POST"}]
    }
    client.post("/channels/", json=channel_data)
    # 处理消息
    response = client.post("/channels/process-test/process", json={"message": "hello"})
    assert response.status_code == 200
    assert "status" in response.json()

def test_process_message_channel_not_found(client):
    response = client.post("/channels/non-existent/process", json={"message": "test"})
    assert response.status_code == 404
    assert "Channel not found" in response.json()["detail"]

def test_process_message_channel_disabled(client):
    channel_data = {
        "id": "disabled-test",
        "name": "Disabled Test Channel",
        "enabled": False,
        "source": {"type": "http", "path": "/disabled", "method": "POST"},
        "destinations": [{"type": "http", "url": "http://disabled", "method": "POST"}]
    }
    client.post("/channels/", json=channel_data)
    response = client.post("/channels/disabled-test/process", json={"message": "test"})
    assert response.status_code == 400
    assert "Channel is disabled" in response.json()["detail"] 