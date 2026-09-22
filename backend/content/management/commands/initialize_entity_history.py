"""Import known evidence and initialize current snapshots without inventing history."""

from django.core.management.base import BaseCommand
from django.db import transaction

from content.models import AccountingChangeLog, ProposalChangeLog
from content.models.entity_history import EntityHistory, EntityRevision
from content.services.entity_history import append_revision, without_history
from content.services.entity_history_registry import ENTITIES, canonical_type, entity_model, snapshot_entity


class Command(BaseCommand):
    help = 'Initialize durable entity history in resumable batches; no historical reconstruction.'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=100)
        parser.add_argument('--entity-type', choices=list(ENTITIES))

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        if batch_size < 1 or batch_size > 1000:
            from django.core.management.base import CommandError
            raise CommandError('batch-size debe estar entre 1 y 1000.')
        kinds = [options['entity_type']] if options['entity_type'] else list(ENTITIES)
        with without_history():
            for kind in kinds:
                self.import_events(kind, batch_size)
                self.import_states(kind, batch_size)
                last_pk = 0
                while True:
                    ids = list(entity_model(kind).objects.filter(pk__gt=last_pk)
                               .order_by('pk').values_list('pk', flat=True)[:batch_size])
                    if not ids:
                        break
                    for pk in ids:
                        with transaction.atomic():
                            entity_model(kind).objects.select_for_update().filter(pk=pk).first()
                            head, _ = EntityHistory.objects.get_or_create(entity_type=kind, object_id=pk)
                            head = EntityHistory.objects.select_for_update().get(pk=head.pk)
                            if head.revision:
                                continue
                            snapshot, secrets, label = snapshot_entity(kind, pk)
                            if snapshot is None:
                                continue
                            head.object_label = label
                            append_revision(head, snapshot=snapshot, secrets=secrets,
                                            action='baseline', changes=[],
                                            identity={'actor_label': 'Estado inicial', 'source': 'baseline'})
                    last_pk = ids[-1]
                self.stdout.write(f'{kind}: historial inicializado')

    def import_events(self, kind, batch_size):
        sources = []
        if kind == 'proposal':
            sources.append(('proposal', ProposalChangeLog.objects.select_related('proposal').all()))
        aliases = [kind, 'collection_account'] if kind == 'document' else [kind]
        sources.append(('accounting', AccountingChangeLog.objects.filter(entity_type__in=aliases)))
        for source, queryset in sources:
            for event in queryset.order_by('pk').iterator(chunk_size=batch_size):
                key = f'{source}:{event.pk}'
                pk = event.proposal_id if source == 'proposal' else event.object_id
                with transaction.atomic():
                    entity_model(kind).objects.select_for_update().filter(pk=pk).first()
                    head, _ = EntityHistory.objects.get_or_create(entity_type=kind, object_id=pk)
                    head = EntityHistory.objects.select_for_update().get(pk=head.pk)
                    # An ordinary write already includes this evidence. Do not
                    # show a second event when re-running the importer later.
                    if any(key in keys for keys in head.entries.exclude(evidence=[])
                           .values_list('evidence', flat=True).iterator(chunk_size=batch_size)):
                        continue
                    if source == 'proposal':
                        changes = [{'field': event.field_name or 'activity', 'label': event.description or 'Actividad',
                                    'old': event.old_value, 'new': event.new_value}]
                        label = event.proposal.title
                        actor = {'seller': 'Vendedor (sin identificar)', 'client': 'Cliente',
                                 'system': 'Sistema'}.get(event.actor_type, 'Autor no registrado')
                        action = event.change_type
                    else:
                        changes, label = event.changes, event.object_repr
                        actor, action = event.actor_username or 'Autor no registrado', event.action
                    EntityRevision.objects.get_or_create(source_key=key, defaults={
                        'history': head, 'occurred_at': event.created_at, 'source': f'legacy:{source}',
                        'action': action, 'actor_label': actor, 'changes': changes, 'evidence': [key],
                        'changed_fields': [{'field': c['field'], 'label': c['label']} for c in changes],
                    })
                    if not head.object_label:
                        head.object_label = label[:255]
                        head.save(update_fields=['object_label'])

    def import_states(self, kind, batch_size):
        if kind not in ('document', 'project'):
            return
        from content.models import DocumentStateEpisodeEvent
        queryset = DocumentStateEpisodeEvent.objects.filter(
            **{f'episode__{kind}__isnull': False},
        ).select_related('episode__state', 'actor')
        for event in queryset.order_by('pk').iterator(chunk_size=batch_size):
            pk = getattr(event.episode, f'{kind}_id')
            key = f'state:{event.pk}'
            with transaction.atomic():
                entity_model(kind).objects.select_for_update().filter(pk=pk).first()
                head, _ = EntityHistory.objects.get_or_create(entity_type=kind, object_id=pk)
                head = EntityHistory.objects.select_for_update().get(pk=head.pk)
                if any(key in keys for keys in head.entries.exclude(evidence=[])
                       .values_list('evidence', flat=True).iterator(chunk_size=batch_size)):
                    continue
                label = f'{event.episode.state.name}: {event.get_event_type_display()}'
                EntityRevision.objects.get_or_create(source_key=key, defaults={
                    'history': head, 'occurred_at': event.recorded_at,
                    'source': 'legacy:state', 'action': event.event_type,
                    'actor_label': (event.actor.get_full_name() or event.actor.username)
                    if event.actor else 'Autor no registrado',
                    'changes': [{'field': 'states', 'label': label, 'old': None, 'new': event.details}],
                    'changed_fields': [{'field': 'states', 'label': label}], 'evidence': [key],
                })
