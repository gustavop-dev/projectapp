"""
LinkedIn OAuth 2.0 + Post Publishing Service.

Handles:
- OAuth 2.0 authorization code flow (3-legged)
- Encrypted token storage via LinkedInToken singleton model
- Automatic token refresh when access token expires
- Publishing blog post summaries with cover images to LinkedIn

LinkedIn API docs:
  - Auth: https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow
  - Posts: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api
"""

import logging
from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LINKEDIN_AUTH_URL = 'https://www.linkedin.com/oauth/v2/authorization'
LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
LINKEDIN_USERINFO_URL = 'https://api.linkedin.com/v2/userinfo'
LINKEDIN_POSTS_URL = 'https://api.linkedin.com/rest/posts'

LINKEDIN_SCOPES = 'openid profile email w_member_social'
LINKEDIN_API_VERSION = '202401'

# LinkedIn refresh tokens last 60 days
_REFRESH_TOKEN_LIFETIME_DAYS = 60


# ---------------------------------------------------------------------------
# Token persistence (encrypted singleton model)
# ---------------------------------------------------------------------------

def _save_token(token_response: dict) -> None:
    """
    Persist token data from LinkedIn token endpoint to the encrypted model.

    Expects keys: access_token, expires_in, and optionally refresh_token.
    """
    from content.models import LinkedInToken

    token = LinkedInToken.load()
    now = timezone.now()

    token.set_access_token(token_response['access_token'])
    token.expires_at = now + timedelta(seconds=token_response.get('expires_in', 5_184_000))
    token.obtained_at = now

    refresh = token_response.get('refresh_token')
    if refresh:
        token.set_refresh_token(refresh)
        token.refresh_token_expires_at = now + timedelta(days=_REFRESH_TOKEN_LIFETIME_DAYS)

    token.save()
    logger.info('LinkedIn token saved (encrypted) — expires at %s.', token.expires_at)


def _clear_token() -> None:
    """Remove all stored token data."""
    from content.models import LinkedInToken

    token = LinkedInToken.load()
    token.clear()
    token.save()
    logger.info('LinkedIn token cleared.')


def _refresh_access_token() -> str | None:
    """
    Attempt to refresh the access token using the stored refresh token.

    Returns the new access token on success, None on failure.
    """
    from content.models import LinkedInToken

    token = LinkedInToken.load()
    refresh_tok = token.get_refresh_token()

    if not refresh_tok or token.is_refresh_expired:
        logger.warning('No valid refresh token available — clearing token.')
        _clear_token()
        return None

    resp = requests.post(
        LINKEDIN_TOKEN_URL,
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_tok,
            'client_id': settings.LINKEDIN_CLIENT_ID,
            'client_secret': settings.LINKEDIN_CLIENT_SECRET,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=15,
    )

    if resp.status_code != 200:
        logger.error('LinkedIn token refresh failed: %s %s', resp.status_code, resp.text)
        _clear_token()
        return None

    data = resp.json()
    now = timezone.now()

    token.set_access_token(data['access_token'])
    token.expires_at = now + timedelta(seconds=data.get('expires_in', 5_184_000))
    token.obtained_at = now
    # LinkedIn does not rotate refresh tokens on refresh
    token.save()

    logger.info('LinkedIn access token refreshed — new expiry %s.', token.expires_at)
    return data['access_token']


# ---------------------------------------------------------------------------
# OAuth 2.0 flow
# ---------------------------------------------------------------------------

def get_authorization_url(state: str = '') -> str:
    """Build the LinkedIn OAuth 2.0 authorization URL."""
    params = {
        'response_type': 'code',
        'client_id': settings.LINKEDIN_CLIENT_ID,
        'redirect_uri': settings.LINKEDIN_REDIRECT_URI,
        'scope': LINKEDIN_SCOPES,
    }
    if state:
        params['state'] = state
    return f'{LINKEDIN_AUTH_URL}?{urlencode(params)}'


def exchange_code_for_token(code: str) -> dict:
    """
    Exchange authorization code for access token.

    Saves the encrypted token to the database.
    Returns the raw token response dict.
    Raises ValueError on failure.
    """
    resp = requests.post(
        LINKEDIN_TOKEN_URL,
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.LINKEDIN_REDIRECT_URI,
            'client_id': settings.LINKEDIN_CLIENT_ID,
            'client_secret': settings.LINKEDIN_CLIENT_SECRET,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=15,
    )
    if resp.status_code != 200:
        logger.error('LinkedIn token exchange failed: %s %s', resp.status_code, resp.text)
        raise ValueError(f'LinkedIn token exchange failed: {resp.text}')

    token_data = resp.json()
    _save_token(token_data)

    # Fetch and cache the user profile
    _cache_profile_info()

    logger.info('LinkedIn access token obtained and encrypted.')
    return token_data


def get_access_token() -> str | None:
    """
    Return the access token, refreshing automatically if expired.

    Returns None if not connected or refresh also failed.
    """
    from content.models import LinkedInToken

    token = LinkedInToken.load()
    access = token.get_access_token()

    if not access:
        return None

    if not token.is_expired:
        return access

    # Token expired — try refresh
    logger.info('LinkedIn access token expired, attempting refresh.')
    return _refresh_access_token()


# ---------------------------------------------------------------------------
# LinkedIn profile
# ---------------------------------------------------------------------------

def _fetch_profile_from_api(access_token: str) -> dict | None:
    """Call LinkedIn userinfo API and return the response dict."""
    resp = requests.get(
        LINKEDIN_USERINFO_URL,
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10,
    )
    if resp.status_code != 200:
        logger.error('LinkedIn profile fetch failed: %s', resp.text)
        return None
    return resp.json()


def _cache_profile_info() -> None:
    """Fetch profile from API and cache it on the token model."""
    from content.models import LinkedInToken

    token = LinkedInToken.load()
    access = token.get_access_token()
    if not access:
        return

    profile = _fetch_profile_from_api(access)
    if not profile:
        return

    token.member_sub = profile.get('sub', '')
    token.profile_name = profile.get('name', '')
    token.profile_picture = profile.get('picture', '')
    token.profile_email = profile.get('email', '')
    token.save(update_fields=[
        'member_sub', 'profile_name', 'profile_picture', 'profile_email',
    ])


def get_member_urn() -> str | None:
    """Return the LinkedIn member URN (urn:li:person:XXX)."""
    from content.models import LinkedInToken

    token = LinkedInToken.load()

    # Use cached sub if available
    if token.member_sub:
        return f'urn:li:person:{token.member_sub}'

    # Fallback: fetch from API
    access = get_access_token()
    if not access:
        return None

    profile = _fetch_profile_from_api(access)
    if not profile or not profile.get('sub'):
        return None

    # Cache for next time
    token.member_sub = profile['sub']
    token.profile_name = profile.get('name', '')
    token.save(update_fields=['member_sub', 'profile_name'])

    return f'urn:li:person:{profile["sub"]}'


# ---------------------------------------------------------------------------
# Publishing
# ---------------------------------------------------------------------------

def publish_blog_to_linkedin(
    summary: str,
    blog_url: str,
    title: str,
    cover_image_url: str = '',
) -> dict:
    """
    Publish a blog post summary to LinkedIn as a link share.

    Args:
        summary: The text content for the LinkedIn post.
        blog_url: Full URL to the blog post on projectapp.co.
        title: Title of the blog post (used in the article preview).
        cover_image_url: URL of the cover image for the article thumbnail.

    Returns:
        dict with 'success', 'post_id' (LinkedIn URN), and 'message'.

    Raises:
        ValueError: If not connected to LinkedIn or missing required data.
    """
    access_token = get_access_token()
    if not access_token:
        raise ValueError('LinkedIn not connected. Please authorize first.')

    member_urn = get_member_urn()
    if not member_urn:
        raise ValueError('Could not retrieve LinkedIn member URN.')

    if not summary:
        raise ValueError('Summary text is required for LinkedIn post.')

    # Build the post payload (LinkedIn Posts API v2)
    post_data = {
        'author': member_urn,
        'commentary': summary,
        'visibility': 'PUBLIC',
        'distribution': {
            'feedDistribution': 'MAIN_FEED',
            'targetEntities': [],
            'thirdPartyDistributionChannels': [],
        },
        'content': {
            'article': {
                'source': blog_url,
                'title': title,
            },
        },
        'lifecycleState': 'PUBLISHED',
        'isReshareDisabledByAuthor': False,
    }

    # Add thumbnail if cover image is available
    if cover_image_url:
        post_data['content']['article']['thumbnail'] = cover_image_url

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
        'LinkedIn-Version': LINKEDIN_API_VERSION,
    }

    resp = requests.post(
        LINKEDIN_POSTS_URL,
        json=post_data,
        headers=headers,
        timeout=15,
    )

    if resp.status_code in (200, 201):
        post_id = resp.headers.get('x-restli-id', '')
        logger.info('LinkedIn post published: %s', post_id)
        return {
            'success': True,
            'post_id': post_id,
            'message': 'Post published to LinkedIn successfully.',
        }

    logger.error('LinkedIn publish failed: %s %s', resp.status_code, resp.text)
    return {
        'success': False,
        'post_id': '',
        'message': f'LinkedIn API error ({resp.status_code}): {resp.text}',
    }


# ---------------------------------------------------------------------------
# Connection status
# ---------------------------------------------------------------------------

def get_connection_status() -> dict:
    """
    Check if LinkedIn is connected and return status info.

    Uses cached profile info from the model to avoid unnecessary API calls.
    Falls back to API call if profile isn't cached.
    """
    from content.models import LinkedInToken

    token = LinkedInToken.load()
    access = token.get_access_token()

    if not access:
        return {'connected': False}

    # Use cached profile info if available
    if token.profile_name:
        return {
            'connected': True,
            'profile_name': token.profile_name,
            'profile_picture': token.profile_picture,
            'email': token.profile_email,
        }

    # Fallback: fetch from API and cache
    profile = _fetch_profile_from_api(access)
    if not profile:
        _clear_token()
        return {'connected': False, 'reason': 'Token expired or invalid.'}

    # Cache profile info
    token.member_sub = profile.get('sub', '')
    token.profile_name = profile.get('name', '')
    token.profile_picture = profile.get('picture', '')
    token.profile_email = profile.get('email', '')
    token.save(update_fields=[
        'member_sub', 'profile_name', 'profile_picture', 'profile_email',
    ])

    return {
        'connected': True,
        'profile_name': token.profile_name,
        'profile_picture': token.profile_picture,
        'email': token.profile_email,
    }
