import pytest
import json
from app import app

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def app_context():
    """Create an application context."""
    with app.app_context():
        yield

def test_index_page(client):
    """Test the main index page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Flask Health Check Application' in response.data
    assert b'Application Status' in response.data

def test_readiness_probe_healthy(client):
    """Test the readiness probe when healthy."""
    response = client.get('/healthz')
    assert response.status_code in [200, 503]  # Can be ready or not ready
    
    data = json.loads(response.data)
    assert 'status' in data
    assert 'timestamp' in data
    assert 'message' in data
    
    if response.status_code == 200:
        assert data['status'] == 'ready'
        assert 'ready to serve traffic' in data['message']
    else:
        assert data['status'] == 'not ready'
        assert 'not ready to serve traffic' in data['message']

def test_liveness_probe_healthy(client):
    """Test the liveness probe when healthy."""
    response = client.get('/failcheck')
    assert response.status_code in [200, 500]  # Can be alive or dead
    
    data = json.loads(response.data)
    assert 'status' in data
    assert 'timestamp' in data
    assert 'message' in data
    
    if response.status_code == 200:
        assert data['status'] == 'alive'
        assert 'alive and healthy' in data['message']
    else:
        assert data['status'] == 'dead'
        assert 'not responding properly' in data['message']

def test_toggle_readiness(client):
    """Test toggling readiness state."""
    response = client.get('/toggle-readiness')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'message' in data
    assert 'ready' in data
    assert isinstance(data['ready'], bool)

def test_toggle_liveness(client):
    """Test toggling liveness state."""
    response = client.get('/toggle-liveness')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'message' in data
    assert 'alive' in data
    assert isinstance(data['alive'], bool)

def test_readiness_probe_states(client):
    """Test both ready and not ready states."""
    # Get current state
    toggle_response = client.get('/toggle-readiness')
    current_state = json.loads(toggle_response.data)['ready']
    
    # Test current state
    health_response = client.get('/healthz')
    health_data = json.loads(health_response.data)
    
    if current_state:
        assert health_response.status_code == 200
        assert health_data['status'] == 'ready'
    else:
        assert health_response.status_code == 503
        assert health_data['status'] == 'not ready'

def test_liveness_probe_states(client):
    """Test both alive and dead states."""
    # Get current state
    toggle_response = client.get('/toggle-liveness')
    current_state = json.loads(toggle_response.data)['alive']
    
    # Test current state
    health_response = client.get('/failcheck')
    health_data = json.loads(health_response.data)
    
    if current_state:
        assert health_response.status_code == 200
        assert health_data['status'] == 'alive'
    else:
        assert health_response.status_code == 500
        assert health_data['status'] == 'dead'

def test_json_response_format(client):
    """Test that health endpoints return valid JSON."""
    endpoints = ['/healthz', '/failcheck', '/toggle-readiness', '/toggle-liveness']
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        try:
            json.loads(response.data)
        except json.JSONDecodeError:
            pytest.fail(f"Endpoint {endpoint} did not return valid JSON")

def test_health_endpoints_have_timestamps(client):
    """Test that health endpoints include timestamps."""
    health_endpoints = ['/healthz', '/failcheck']
    
    for endpoint in health_endpoints:
        response = client.get(endpoint)
        data = json.loads(response.data)
        assert 'timestamp' in data
        # Verify timestamp format (ISO format)
        from datetime import datetime
        try:
            datetime.fromisoformat(data['timestamp'])
        except ValueError:
            pytest.fail(f"Invalid timestamp format in {endpoint}")

def test_application_configuration(app_context):
    """Test application configuration."""
    assert app.config['TESTING'] is True
    
def test_concurrent_health_checks(client):
    """Test multiple concurrent health check requests."""
    import threading
    results = []
    
    def check_health():
        response = client.get('/healthz')
        results.append(response.status_code)
    
    # Start multiple threads
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=check_health)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # All requests should return valid status codes
    assert len(results) == 5
    for status_code in results:
        assert status_code in [200, 503]

def test_app_globals_state():
    """Test global application state variables."""
    from app import app_ready, app_alive
    assert isinstance(app_ready, bool)
    assert isinstance(app_alive, bool)

def test_index_page_content(client):
    """Test specific content on index page."""
    response = client.get('/')
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert 'Current Time:' in content
    assert 'Readiness Probe' in content
    assert 'Liveness Probe' in content
    assert '/healthz' in content
    assert '/failcheck' in content
