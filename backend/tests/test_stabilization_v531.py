def test_security_headers(client):
    response=client.get('/ping')
    assert response.status_code==200
    assert response.headers['x-content-type-options']=='nosniff'
    assert response.headers['x-frame-options']=='DENY'
    assert 'content-security-policy' in response.headers

def test_metrics(client):
    client.get('/ping')
    response=client.get('/metrics')
    assert response.status_code==200
    assert 'cs_platform_http_requests_total' in response.text

def test_request_context(client):
    response=client.get('/ping',headers={'X-Request-ID':'test-req'})
    assert response.headers['x-request-id']=='test-req'
    assert 'x-response-time-ms' in response.headers
