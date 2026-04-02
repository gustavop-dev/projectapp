"""
post_delete signals: remove physical files from storage when DB records are deleted.
Prevents orphaned files in media/ after hard deletes.
"""

from django.db.models.signals import post_delete
from django.dispatch import receiver

from accounts.models import (
    BugReport,
    ChangeRequest,
    Deliverable,
    DeliverableClientUpload,
    DeliverableFile,
    DeliverableVersion,
    UserProfile,
)


def _delete_file(field):
    """Delete a FileField/ImageField file from storage if it has a value."""
    if field and field.name:
        try:
            field.storage.delete(field.name)
        except Exception:
            pass


@receiver(post_delete, sender=UserProfile)
def delete_user_profile_files(sender, instance, **kwargs):
    _delete_file(instance.avatar)
    _delete_file(instance.custom_cover_image)


@receiver(post_delete, sender=ChangeRequest)
def delete_change_request_files(sender, instance, **kwargs):
    _delete_file(instance.screenshot)


@receiver(post_delete, sender=BugReport)
def delete_bug_report_files(sender, instance, **kwargs):
    _delete_file(instance.screenshot)


@receiver(post_delete, sender=Deliverable)
def delete_deliverable_files(sender, instance, **kwargs):
    _delete_file(instance.file)


@receiver(post_delete, sender=DeliverableVersion)
def delete_deliverable_version_files(sender, instance, **kwargs):
    _delete_file(instance.file)


@receiver(post_delete, sender=DeliverableFile)
def delete_deliverable_attachment_files(sender, instance, **kwargs):
    _delete_file(instance.file)


@receiver(post_delete, sender=DeliverableClientUpload)
def delete_deliverable_client_upload_files(sender, instance, **kwargs):
    _delete_file(instance.file)
