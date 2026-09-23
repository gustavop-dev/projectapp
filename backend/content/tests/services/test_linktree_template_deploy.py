"""A healthy homepage must not conceal missing template API routes during deploy."""
import importlib.util
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[4] / 'scripts' / 'check-template-deploy.py'
spec = importlib.util.spec_from_file_location('check_template_deploy', MODULE_PATH)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


@pytest.fixture
def api_server():
    """Serve actual HTTP errors/successes without touching the production server."""
    state = {'status': 401, 'type': 'application/json', 'body': b'{"detail":"Authentication required"}', 'requests': []}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            state['requests'].append(self.path)
            self.send_response(state['status'])
            self.send_header('Content-Type', state['type'])
            self.end_headers()
            self.wfile.write(state['body'])

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_deploy_accepts_protected_template_api(api_server):
    """A real DRF-style authentication response establishes that the route exists."""
    url, state = api_server

    deploy.check_template_api(url)

    assert state['requests'] == ['/api/linktrees/admin/11111111-1111-4111-8111-111111111111/templates/']


@pytest.mark.parametrize(('status', 'content_type', 'body'), [
    (200, 'text/html', b'<html>Nuxt homepage</html>'),
    (401, 'text/html', b'<html>Unauthorized</html>'),
    (401, 'application/json', b'not json'),
    (401, 'application/json', b'[]'),
    (401, 'application/json', b'{"detail":""}'),
    (500, 'application/json', b'{"detail":"Server error"}'),
])
def test_deploy_rejects_missing_or_broken_template_api(api_server, status, content_type, body):
    """Reject SPA fallbacks, proxy errors and malformed auth responses."""
    url, state = api_server
    state.update(status=status, type=content_type, body=body)

    with pytest.raises(ValueError, match=r'Template API returned|Expecting value'):
        deploy.check_template_api(url)
