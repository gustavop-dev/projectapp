#!/usr/bin/env python3
"""Read-only smoke check: an SPA fallback must never pass as the template API."""
import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check_template_api(base_url):
    path = '/api/linktrees/admin/11111111-1111-4111-8111-111111111111/templates/'
    request = Request(base_url.rstrip('/') + path, headers={'Accept': 'application/json'})
    try:
        response = urlopen(request, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        payload = response.read(65536)
        content_type = response.headers.get_content_type()
        # An anonymous request must reach DRF's authentication boundary.
        if response.status != 401 or content_type != 'application/json':
            raise ValueError(f'Template API returned {response.status} {content_type}; expected 401 application/json.')
        body = json.loads(payload)
        if not isinstance(body, dict) or not isinstance(body.get('detail'), str) or not body['detail']:
            raise ValueError('Template API returned an invalid authentication response.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='https://www.projectapp.co')
    args = parser.parse_args()
    try:
        check_template_api(args.url)
    except (OSError, URLError, ValueError) as error:
        parser.exit(1, f'Template deployment check failed: {error}\n')
    print('Template API health check passed (anonymous access protected).')


if __name__ == '__main__':
    main()
