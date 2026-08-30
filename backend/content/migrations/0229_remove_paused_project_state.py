from decimal import Decimal

from django.db import migrations, models
from django.db.migrations.exceptions import IrreversibleError
from django.db.models import Sum
from django.utils import timezone


PROJECT_STATUS_BY_EFFECT = {
    'development': 'development',
    'operating': 'active',
    'suspended': 'suspended',
    'completed': 'completed',
    'decommissioned': 'decommissioned',
}
OPEN_PAYMENT_STATUSES = ('pending', 'processing', 'failed', 'overdue')
CANONICAL_PROJECT_STATE_ORDER = {
    'development': 0,
    'active': 1,
    'evolving': 2,
    'suspended': 3,
    'completed': 4,
    'decommissioned': 5,
}


def _cancel_future_billing(
    IncomeRecord,
    ExpenseRecord,
    Payment,
    project_ids,
    *,
    alias,
    now,
):
    if not project_ids:
        return

    today = timezone.localdate(now)
    future_incomes = IncomeRecord.objects.using(alias).filter(
        project_id__in=project_ids,
        kind='expected',
        period_date__gt=today,
    )
    cancellable_ids = []
    for income in future_incomes.iterator():
        liquid_total = (
            IncomeRecord.objects.using(alias)
            .filter(expected_income_id=income.pk, kind='liquid')
            .aggregate(total=Sum('total_amount'))['total']
            or Decimal('0')
        )
        deduction_total = (
            ExpenseRecord.objects.using(alias)
            .filter(source_income_id=income.pk)
            .exclude(deduction_type='')
            .aggregate(total=Sum('total_amount'))['total']
            or Decimal('0')
        )
        if liquid_total + deduction_total == 0:
            cancellable_ids.append(income.pk)

    if cancellable_ids:
        IncomeRecord.objects.using(alias).filter(pk__in=cancellable_ids).update(
            kind='cancelled',
            reminders_muted=True,
            reminders_muted_until=None,
        )

    Payment.objects.using(alias).filter(
        subscription__project_id__in=project_ids,
        status__in=OPEN_PAYMENT_STATUSES,
        is_archived=False,
        due_date__gt=today,
    ).update(is_archived=True, archived_at=now)


def consolidate_paused_project_state(apps, schema_editor):
    alias = schema_editor.connection.alias
    DocumentState = apps.get_model('content', 'DocumentState')
    DocumentStateEpisode = apps.get_model('content', 'DocumentStateEpisode')
    DocumentStateEpisodeEvent = apps.get_model(
        'content',
        'DocumentStateEpisodeEvent',
    )
    IncomeRecord = apps.get_model('content', 'IncomeRecord')
    ExpenseRecord = apps.get_model('content', 'ExpenseRecord')
    Project = apps.get_model('accounts', 'Project')
    Payment = apps.get_model('accounts', 'Payment')

    suspended = (
        DocumentState.objects.using(alias)
        .filter(catalog='projects', system_key='suspended')
        .first()
    )
    if suspended is None:
        raise RuntimeError(
            'Cannot remove Pausado because the project catalog has no '
            'Suspendido seed state.',
        )

    paused_states = list(
        DocumentState.objects.using(alias)
        .filter(catalog='projects', operational_effect='paused')
        .exclude(pk=suspended.pk)
        .order_by('id')
    )
    paused_state_ids = [state.pk for state in paused_states]
    now = timezone.now()

    # Repair a stale compatibility mirror without replacing a different
    # canonical current state.
    for effect, status in PROJECT_STATUS_BY_EFFECT.items():
        Project.objects.using(alias).filter(
            status='paused',
            current_state__operational_effect=effect,
        ).update(status=status)

    affected_project_ids = set(
        Project.objects.using(alias)
        .filter(current_state_id__in=paused_state_ids)
        .values_list('id', flat=True)
    )
    unclassified_project_ids = list(
        Project.objects.using(alias)
        .filter(status='paused', current_state_id__isnull=True)
        .values_list('id', flat=True)
    )
    affected_project_ids.update(unclassified_project_ids)

    # Preserve a dated audit fact before the old catalog rows disappear.
    for source in paused_states:
        episodes = DocumentStateEpisode.objects.using(alias).filter(
            state_id=source.pk,
        )
        for episode_id in episodes.values_list('id', flat=True).iterator():
            DocumentStateEpisodeEvent.objects.using(alias).create(
                episode_id=episode_id,
                event_type='merged',
                effective_at=now,
                details={
                    'reason': 'paused_state_removed',
                    'source_state_id': source.pk,
                    'source_state_name': source.name,
                    'target_state_id': suspended.pk,
                    'target_state_name': suspended.name,
                },
            )
        episodes.update(state_id=suspended.pk)
        DocumentStateEpisode.objects.using(alias).filter(
            project__isnull=False,
            close_note=f'Transición a {source.name}',
        ).update(close_note=f'Transición a {suspended.name}')
        DocumentState.objects.using(alias).filter(
            merged_into_id=source.pk,
        ).update(merged_into_id=suspended.pk)

    # A pre-catalog row with only the old mirror receives truthful migration
    # history instead of silently gaining a current state with no episode.
    for project_id in unclassified_project_ids:
        episode = DocumentStateEpisode.objects.using(alias).create(
            project_id=project_id,
            state_id=suspended.pk,
            opened_at=None,
            origin='migration',
        )
        DocumentStateEpisodeEvent.objects.using(alias).create(
            episode_id=episode.pk,
            event_type='opened',
            effective_at=None,
            details={
                'origin': 'migration',
                'opening_time_known': False,
                'legacy_status': 'paused',
                'consolidated_to': 'suspended',
            },
        )

    if affected_project_ids:
        Project.objects.using(alias).filter(
            pk__in=affected_project_ids,
        ).update(
            current_state_id=suspended.pk,
            status='suspended',
            state_review_required=False,
        )
        _cancel_future_billing(
            IncomeRecord,
            ExpenseRecord,
            Payment,
            affected_project_ids,
            alias=alias,
            now=now,
        )

    # No compatibility value or hidden custom effect may survive the rollout.
    remaining_legacy = Project.objects.using(alias).filter(status='paused')
    if remaining_legacy.exists():
        raise RuntimeError(
            'Cannot remove Pausado while projects still use the legacy status.',
        )

    if paused_state_ids:
        DocumentState.objects.using(alias).filter(
            pk__in=paused_state_ids,
        ).delete()

    for system_key, order in CANONICAL_PROJECT_STATE_ORDER.items():
        DocumentState.objects.using(alias).filter(
            catalog='projects',
            system_key=system_key,
        ).update(order=order)


def restore_paused_project_state(_apps, _schema_editor):
    raise IrreversibleError(
        'Pausado was consolidated into Suspendido and its historical '
        'associations cannot be split safely.',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0057_userprofile_document_navigation_mode'),
        ('content', '0228_emaillinksnapshot_url_sha256'),
    ]

    operations = [
        migrations.RunPython(
            consolidate_paused_project_state,
            restore_paused_project_state,
        ),
        migrations.AlterField(
            model_name='documentstate',
            name='operational_effect',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'Sin efecto automático'),
                    ('development', 'En desarrollo'),
                    ('operating', 'Operativo'),
                    ('suspended', 'Cobros suspendidos'),
                    ('completed', 'Cierre correcto'),
                    ('decommissioned', 'Baja definitiva'),
                ],
                default='',
                help_text=(
                    'Project-side consequence policy; blank for document states.'
                ),
                max_length=20,
            ),
        ),
    ]
