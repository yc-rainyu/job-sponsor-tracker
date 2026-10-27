def test_health_ok(client):
    response = client.get('/health')
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'ok'
    assert body['db'] == 'ok'
    assert body['version']


def test_health_head(client):
    response = client.head('/health')
    assert response.status_code == 200
    assert response.content == b''
