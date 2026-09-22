"""Relations and legacy evidence that complement the explicit ORM boundary."""

from django.contrib.auth import get_user_model
from django.db.models import SET_NULL
from django.db.models.signals import m2m_changed, pre_delete, pre_save, post_save
from django.dispatch import receiver

from content.models import AccountingChangeLog, Document, ProposalChangeLog, DocumentStateEpisodeEvent
from content.services.entity_history import capture, capture_instance, history_active, link_evidence
from content.services.entity_history_registry import canonical_type, ENTITIES


@receiver(pre_save, sender=get_user_model())
def capture_client_identity(sender, instance, raw=False, update_fields=None, **kwargs):
    if not raw and (update_fields is None or set(update_fields) & {'first_name', 'last_name', 'email'}):
        capture_instance(instance)


@receiver(pre_delete)
def capture_cascade(sender, instance, **kwargs):
    # Called within the deleting model's history operation or the HTTP boundary.
    if not history_active():
        return
    capture_instance(instance)
    from content.models.history_tracked import HistoryTrackedModel
    # Django's deletion collector clears nullable FKs through a base manager,
    # bypassing the public QuerySet override. Capture those dependents here.
    for relation in instance._meta.related_objects:
        field = relation.field
        if (getattr(field.remote_field, 'on_delete', None) is SET_NULL
                and issubclass(relation.related_model, HistoryTrackedModel)):
            for dependent in relation.related_model.objects.filter(
                    **{field.attname: instance.pk}).order_by('pk'):
                capture_instance(dependent)


@receiver(m2m_changed, sender=Document.tags.through)
def capture_document_tags(sender, instance, action, reverse, pk_set, **kwargs):
    if not action.startswith('pre_'):
        return
    if reverse:
        ids = pk_set if pk_set is not None else instance.documents.values_list('pk', flat=True)
    else:
        ids = [instance.pk]
    for pk in sorted(ids):
        capture('document', pk)


@receiver(post_save, sender=AccountingChangeLog)
def link_accounting_event(sender, instance, created, raw=False, **kwargs):
    kind = canonical_type(instance.entity_type)
    if created and not raw and kind in ENTITIES:
        link_evidence(kind, instance.object_id, f'accounting:{instance.pk}')


@receiver(post_save, sender=ProposalChangeLog)
def link_proposal_event(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        link_evidence('proposal', instance.proposal_id, f'proposal:{instance.pk}')


@receiver(post_save, sender=DocumentStateEpisodeEvent)
def link_state_event(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        for kind in ('document', 'project'):
            pk = getattr(instance.episode, f'{kind}_id')
            if pk:
                link_evidence(kind, pk, f'state:{instance.pk}')
