"""
post_delete signals: remove physical files from storage when DB records are deleted.
post_save signals: guarantee UserProfile invariant and keep BusinessProposal
client snapshots in sync with the canonical UserProfile/User identity.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_delete, post_save
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

User = get_user_model()

# Fields whose mutation must propagate to BusinessProposal/WebAppDiagnostic
# client snapshots. Anything else (last_login, is_active, password, …) is
# irrelevant and should not trigger the bulk-update cascade.
_SNAPSHOT_USER_FIELDS = frozenset({'first_name', 'last_name', 'email'})
_SNAPSHOT_PROFILE_FIELDS = frozenset({'phone', 'company_name'})


def _touches_snapshot(update_fields, snapshot_fields):
    """True when a save() touches at least one snapshot-relevant field.

    ``update_fields=None`` means "full save" — assume snapshot fields could
    have changed and run the sync.
    """
    if update_fields is None:
        return True
    return bool(set(update_fields) & snapshot_fields)


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


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, raw=False, **kwargs):
    """Guarantee every User ends up with a UserProfile.

    Most code paths (onboarding, proposal client service, seed commands)
    create the profile explicitly. This is the safety net for paths that do
    not — notably ``manage.py createsuperuser``. Deferred via
    ``transaction.on_commit`` so it never races with explicit profile
    creation inside the same transaction (the profile already exists at
    commit time, making this a no-op).
    """
    if raw or not created:
        return

    user_id = instance.pk
    is_superuser = instance.is_superuser

    def _ensure():
        if UserProfile.objects.filter(user_id=user_id).exists():
            return
        UserProfile.objects.create(
            user_id=user_id,
            role=UserProfile.ROLE_ADMIN if is_superuser else UserProfile.ROLE_CLIENT,
        )

    transaction.on_commit(_ensure)


@receiver(post_save, sender=UserProfile)
def sync_proposals_on_profile_save(
    sender, instance, created, raw=False, update_fields=None, **kwargs,
):
    """Refresh BusinessProposal/WebAppDiagnostic client snapshots whenever a
    client profile's identity fields are mutated.
    """
    if raw or created or instance.role != UserProfile.ROLE_CLIENT:
        return
    if not _touches_snapshot(update_fields, _SNAPSHOT_PROFILE_FIELDS):
        return
    from accounts.services.proposal_client_service import sync_snapshot_for_profile
    sync_snapshot_for_profile(instance)


@receiver(post_save, sender=User)
def sync_proposals_on_user_save(
    sender, instance, created, raw=False, update_fields=None, **kwargs,
):
    """Refresh proposal/diagnostic snapshots when User identity fields change.

    Skipped for ``last_login``-only saves (every login) and similar
    non-snapshot mutations to avoid bulk-updating every linked proposal on
    routine activity.
    """
    if raw or created:
        return
    if not _touches_snapshot(update_fields, _SNAPSHOT_USER_FIELDS):
        return
    profile = getattr(instance, 'profile', None)
    if profile and profile.role == UserProfile.ROLE_CLIENT:
        from accounts.services.proposal_client_service import sync_snapshot_for_profile
        sync_snapshot_for_profile(profile)


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
