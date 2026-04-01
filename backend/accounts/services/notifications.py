"""
Notification service — creates in-app notifications for platform events.

Usage:
    from accounts.services.notifications import notify

    notify(
        user=client_user,
        type=Notification.TYPE_BUG_REPORTED,
        title='Nuevo bug reportado',
        message='Carlos reportó "Botón no funciona" en Plataforma E-commerce.',
        project=project,
        related_object_type='bug_report',
        related_object_id=bug.id,
    )
"""

from accounts.models import Notification, Project, UserProfile


def notify(
    user,
    type,
    title,
    message='',
    project=None,
    deliverable=None,
    related_object_type='',
    related_object_id=None,
):
    """Create a single notification for a user."""
    return Notification.objects.create(
        user=user,
        type=type,
        title=title,
        message=message,
        project=project,
        deliverable=deliverable,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
    )


def notify_project_admins(
    project,
    type,
    title,
    message='',
    related_object_type='',
    related_object_id=None,
    exclude_user=None,
    deliverable=None,
):
    """Notify all admin users about an event in a project."""
    admin_profiles = UserProfile.objects.filter(role=UserProfile.ROLE_ADMIN).select_related('user')
    notifications = []
    for profile in admin_profiles:
        if exclude_user and profile.user_id == exclude_user.id:
            continue
        notifications.append(Notification(
            user=profile.user,
            type=type,
            title=title,
            message=message,
            project=project,
            deliverable=deliverable,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
        ))
    if notifications:
        Notification.objects.bulk_create(notifications)
    return notifications


def notify_project_client(
    project,
    type,
    title,
    message='',
    related_object_type='',
    related_object_id=None,
    exclude_user=None,
    deliverable=None,
):
    """Notify the project's client about an event."""
    client = project.client
    if exclude_user and client.id == exclude_user.id:
        return None
    return notify(
        user=client,
        type=type,
        title=title,
        message=message,
        project=project,
        deliverable=deliverable,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
    )
