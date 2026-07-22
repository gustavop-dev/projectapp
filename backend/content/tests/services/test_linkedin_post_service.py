"""publish_post_to_linkedin: payload shape and error paths (all HTTP mocked)."""
from unittest.mock import MagicMock, patch

import pytest

from content.services.linkedin_service import publish_post_to_linkedin

MOD = 'content.services.linkedin_service'


def _ok_response(post_id='urn:li:share:123'):
    resp = MagicMock()
    resp.status_code = 201
    resp.headers = {'x-restli-id': post_id}
    return resp


@patch(f'{MOD}.requests.post')
@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_text_only_post_omits_content_key(mock_tok, mock_urn, mock_post):
    mock_post.return_value = _ok_response()
    result = publish_post_to_linkedin('Hola mundo')
    assert result['success'] is True
    assert result['post_id'] == 'urn:li:share:123'
    payload = mock_post.call_args.kwargs['json']
    assert payload['author'] == 'urn:li:person:abc'
    assert payload['commentary'] == 'Hola mundo'
    assert payload['lifecycleState'] == 'PUBLISHED'
    assert 'content' not in payload


@patch(f'{MOD}._upload_image_to_linkedin', return_value='urn:li:image:img1')
@patch(f'{MOD}.requests.post')
@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_image_post_attaches_media_urn(mock_tok, mock_urn, mock_post, mock_upload):
    mock_post.return_value = _ok_response()
    result = publish_post_to_linkedin('Con imagen', image_url='https://projectapp.co/media/x.jpg')
    assert result['success'] is True
    payload = mock_post.call_args.kwargs['json']
    assert payload['content'] == {'media': {'id': 'urn:li:image:img1'}}


@patch(f'{MOD}._upload_image_to_linkedin', return_value=None)
@patch(f'{MOD}.requests.post')
@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_failed_image_upload_publishes_text_only(mock_tok, mock_urn, mock_post, mock_upload):
    mock_post.return_value = _ok_response()
    result = publish_post_to_linkedin('Texto', image_url='https://projectapp.co/media/x.jpg')
    assert result['success'] is True
    assert 'content' not in mock_post.call_args.kwargs['json']


@patch(f'{MOD}.get_access_token', return_value=None)
def test_not_connected_raises(mock_tok):
    with pytest.raises(ValueError) as exc_info:
        publish_post_to_linkedin('Hola')
    assert 'not connected' in str(exc_info.value)


@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_empty_commentary_raises(mock_tok, mock_urn):
    with pytest.raises(ValueError) as exc_info:
        publish_post_to_linkedin('')
    assert 'required' in str(exc_info.value)


@patch(f'{MOD}.requests.post')
@patch(f'{MOD}.get_member_urn', return_value='urn:li:person:abc')
@patch(f'{MOD}.get_access_token', return_value='tok')
def test_api_error_returns_failure_dict(mock_tok, mock_urn, mock_post):
    resp = MagicMock()
    resp.status_code = 422
    resp.text = 'UNPROCESSABLE_ENTITY'
    mock_post.return_value = resp
    result = publish_post_to_linkedin('Hola')
    assert result['success'] is False
    assert '422' in result['message']
    mock_post.assert_called_once()
