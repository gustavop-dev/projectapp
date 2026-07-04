"""Scheduling and publishing helpers for freeform LinkedIn posts.

Mirrors the blog pattern: per-post Huey ETA task enqueued on save plus a
periodic sweep, with an atomic status transition as the double-publish
guard.
"""
import logging

from django.utils import timezone

from content.services.linkedin_service import publish_post_to_linkedin

logger = logging.getLogger(__name__)

LINKEDIN_MEDIA_BASE = 'https://projectapp.co'


def publish_linkedin_post_now(post) -> dict:
    """
    Publish a freeform post with an atomic double-publish guard.

    Claims the post by flipping status to 'published' first (0 rows updated
    means someone else already published it); on API failure reverts to
    'failed' and persists the error message.
    """
    from content.models import LinkedInPost

    claimed = LinkedInPost.objects.filter(pk=post.id).exclude(
        status=LinkedInPost.STATUS_PUBLISHED,
    ).update(status=LinkedInPost.STATUS_PUBLISHED)
    if not claimed:
        return {'success': False, 'already': True,
                'message': 'Este post ya fue publicado en LinkedIn.'}

    image_url = ''
    if post.image:
        image_url = f'{LINKEDIN_MEDIA_BASE}{post.image.url}'

    try:
        result = publish_post_to_linkedin(post.commentary, image_url=image_url)
    except ValueError as exc:
        LinkedInPost.objects.filter(pk=post.id).update(
            status=LinkedInPost.STATUS_FAILED, error_message=str(exc),
        )
        return {'success': False, 'not_connected': True, 'message': str(exc)}

    if result['success']:
        LinkedInPost.objects.filter(pk=post.id).update(
            status=LinkedInPost.STATUS_PUBLISHED,
            linkedin_post_id=result['post_id'],
            published_at=timezone.now(),
            error_message='',
        )
    else:
        LinkedInPost.objects.filter(pk=post.id).update(
            status=LinkedInPost.STATUS_FAILED,
            error_message=result['message'],
        )
    return result


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


def apply_schedule_transition(post):
    """Sync status with scheduled_at after create/update and enqueue ETA.

    Shared by the panel views and the MCP handlers so scheduling rules
    live in one place.
    """
    from content.models import LinkedInPost

    if post.status == LinkedInPost.STATUS_PUBLISHED:
        return
    if post.scheduled_at:
        post.status = LinkedInPost.STATUS_SCHEDULED
        post.save(update_fields=['status', 'updated_at'])
        schedule_linkedin_post_eta(post)
    elif post.status == LinkedInPost.STATUS_SCHEDULED:
        post.status = LinkedInPost.STATUS_DRAFT
        post.save(update_fields=['status', 'updated_at'])
