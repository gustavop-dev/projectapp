"""
post_delete signals: remove physical files from storage when DB records are deleted.
Prevents orphaned files in media/ after hard deletes.
"""

from django.db.models.signals import post_delete
from django.dispatch import receiver

from content.models.blog_post import BlogPost
from content.models.issuer_profile import IssuerProfile
from content.models.portfolio_works import PortfolioWork


def _delete_file(field):
    """Delete a FileField/ImageField file from storage if it has a value."""
    if field and field.name:
        try:
            field.storage.delete(field.name)
        except Exception:
            pass


@receiver(post_delete, sender=BlogPost)
def delete_blog_post_files(sender, instance, **kwargs):
    _delete_file(instance.cover_image)


@receiver(post_delete, sender=PortfolioWork)
def delete_portfolio_work_files(sender, instance, **kwargs):
    _delete_file(instance.cover_image)


@receiver(post_delete, sender=IssuerProfile)
def delete_issuer_profile_files(sender, instance, **kwargs):
    _delete_file(instance.logo)
