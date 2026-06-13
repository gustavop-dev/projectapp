"""
Frontend prerender rebuild service.

The public site is a static `nuxi generate` build served by Django from
backend/static/frontend/ (see projectapp.views.serve_nuxt). Blog posts are
prerendered into that build, so the static HTML goes stale whenever published
blog content changes. This service runs the frontend build (which fetches the
current slugs from the API and atomically swaps the output dir) and tracks the
last successful build in a marker file so unnecessary rebuilds are skipped.

No service restarts are involved: serve_nuxt reads the files from disk on
every request, and collectstatic only copies hashed assets.
"""
import json
import logging
import os
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(settings.BASE_DIR).parent / 'frontend'
MARKER_PATH = Path(settings.BASE_DIR) / 'logs' / 'frontend-build-marker.json'
BUILD_TIMEOUT_SECONDS = 30 * 60


def latest_published_change():
    """Most recent updated_at among published posts, or None."""
    from content.models import BlogPost
    post = (
        BlogPost.objects.filter(is_published=True)
        .order_by('-updated_at')
        .first()
    )
    return post.updated_at if post else None


def last_build_started_at():
    """Start time of the last successful build, or None if never built."""
    try:
        data = json.loads(MARKER_PATH.read_text())
        return parse_datetime(data.get('started_at') or '')
    except (OSError, ValueError):
        return None


def _write_marker(started_at):
    MARKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKER_PATH.write_text(json.dumps({'started_at': started_at.isoformat()}))


def rebuild_needed():
    """True when published blog content changed after the last build started.

    Using the build *start* time means content edited mid-build (and therefore
    possibly missing from that build's API snapshot) still triggers the next
    rebuild.
    """
    latest = latest_published_change()
    if latest is None:
        return False
    last = last_build_started_at()
    return last is None or latest > last


def run_frontend_rebuild(force=False):
    """Run the static frontend build and swap it live.

    Returns {'status': 'success'|'skipped'|'failed', 'detail': str}.
    """
    if not settings.FRONTEND_REBUILD_ENABLED:
        return {'status': 'skipped', 'detail': 'FRONTEND_REBUILD_ENABLED is off'}
    if not force and not rebuild_needed():
        return {'status': 'skipped', 'detail': 'no published changes since last build'}

    started_at = timezone.now()
    env = os.environ.copy()
    env.setdefault('PRERENDER_API_ORIGIN', settings.PRERENDER_API_ORIGIN)
    # A production build that silently drops the prerendered posts is a
    # regression — make the build fail instead (see nuxt.config.ts).
    env.setdefault('PRERENDER_REQUIRE_BLOG', '0' if settings.DEBUG else '1')

    logger.info(
        '[FrontendRebuild] starting: %s (cwd=%s, api=%s)',
        settings.FRONTEND_BUILD_COMMAND, FRONTEND_DIR, env['PRERENDER_API_ORIGIN'],
    )
    try:
        result = subprocess.run(
            settings.FRONTEND_BUILD_COMMAND,
            shell=True,
            cwd=FRONTEND_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=BUILD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        logger.error('[FrontendRebuild] build timed out after %ss', BUILD_TIMEOUT_SECONDS)
        return {'status': 'failed', 'detail': f'timeout after {BUILD_TIMEOUT_SECONDS}s'}

    if result.returncode != 0:
        tail = (result.stderr or result.stdout or '')[-2000:]
        logger.error('[FrontendRebuild] build failed (rc=%s): %s', result.returncode, tail)
        return {'status': 'failed', 'detail': tail}

    if not settings.DEBUG:
        call_command('collectstatic', interactive=False, verbosity=0)

    _write_marker(started_at)
    logger.info('[FrontendRebuild] success (started_at=%s)', started_at.isoformat())
    return {'status': 'success', 'detail': ''}


def schedule_rebuild_after_publish(delay_seconds=120):
    """Enqueue a frontend rebuild shortly after a publish-state change.

    The small delay lets bursts of consecutive saves coalesce: the first task
    to run rebuilds with everything published so far, and the rest see a
    fresh marker and skip. Never raises — a failed enqueue must not break the
    publish flow it hooks into.
    """
    if not settings.FRONTEND_REBUILD_ENABLED:
        return
    try:
        from content.tasks import rebuild_frontend_prerender
        rebuild_frontend_prerender.schedule(delay=delay_seconds)
        logger.info('[FrontendRebuild] rebuild enqueued (delay=%ss)', delay_seconds)
    except Exception:
        logger.exception('[FrontendRebuild] failed to enqueue rebuild')
