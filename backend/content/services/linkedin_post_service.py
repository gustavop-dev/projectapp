"""Scheduling and publishing helpers for freeform LinkedIn posts.

Mirrors the blog pattern: per-post Huey ETA task enqueued on save plus a
periodic sweep, with an atomic status transition as the double-publish
guard.
"""
import logging

logger = logging.getLogger(__name__)


def schedule_linkedin_post_eta(post):
    """Enqueue the per-post ETA publish task (Huey)."""
    from content.tasks import publish_single_scheduled_linkedin_post
    publish_single_scheduled_linkedin_post.schedule(
        args=(post.id,), eta=post.scheduled_at,
    )
    logger.info(
        'Encolado publish_single_scheduled_linkedin_post para post %s a %s',
        post.id, post.scheduled_at,
    )
