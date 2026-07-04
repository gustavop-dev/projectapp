"""
Freeform LinkedIn posts created from /panel/linkedin.

Independent from BlogPost: these posts have their own text (commentary),
optional image, and a draft -> scheduled -> published lifecycle handled
by Huey tasks (mirroring the blog scheduling pattern).
"""

from django.db import models

LINKEDIN_COMMENTARY_MAX_LENGTH = 3000  # LinkedIn Posts API commentary limit


class LinkedInPost(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_PUBLISHED = 'published'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_FAILED, 'Failed'),
    ]

    commentary = models.TextField(
        max_length=LINKEDIN_COMMENTARY_MAX_LENGTH,
        help_text='Post text (LinkedIn commentary, max 3000 chars).',
    )
    image = models.ImageField(
        upload_to='linkedin_posts/', blank=True, null=True,
        help_text='Optional image attached to the post.',
    )
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default=STATUS_DRAFT,
    )
    scheduled_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When set (and status=scheduled), Huey publishes at this time.',
    )
    published_at = models.DateTimeField(null=True, blank=True)
    linkedin_post_id = models.CharField(
        max_length=255, blank=True, default='',
        help_text='LinkedIn URN returned on publish (x-restli-id).',
    )
    error_message = models.TextField(
        blank=True, default='',
        help_text='Last publish failure detail.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'LinkedIn post'
        verbose_name_plural = 'LinkedIn posts'

    def __str__(self):
        return self.commentary[:40]
