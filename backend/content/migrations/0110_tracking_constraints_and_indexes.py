from django.db import migrations, models


def dedupe_view_events(apps, schema_editor):
    """Collapse duplicate (proposal, session_id) and (diagnostic, session_id)
    rows — if any — before applying the unique constraints.

    Keeps the most recent row (highest id / viewed_at) and reparents child
    section views onto it, then deletes the older duplicates. No-op if there
    are no duplicates, which is the common case.
    """
    ProposalViewEvent = apps.get_model('content', 'ProposalViewEvent')
    ProposalSectionView = apps.get_model('content', 'ProposalSectionView')
    DiagnosticViewEvent = apps.get_model('content', 'DiagnosticViewEvent')
    DiagnosticSectionView = apps.get_model('content', 'DiagnosticSectionView')

    def _collapse(event_model, section_model, group_field):
        seen = {}
        for event in event_model.objects.all().order_by(group_field, 'session_id', 'viewed_at', 'id'):
            key = (getattr(event, f'{group_field}_id'), event.session_id)
            prev = seen.get(key)
            if prev is None:
                seen[key] = event
                continue
            # `event` is more recent — reparent children from `prev` and drop it
            section_model.objects.filter(view_event_id=prev.id).update(view_event_id=event.id)
            prev.delete()
            seen[key] = event

    _collapse(ProposalViewEvent, ProposalSectionView, 'proposal')
    _collapse(DiagnosticViewEvent, DiagnosticSectionView, 'diagnostic')


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0109_fix_corporate_branding_backfill'),
    ]

    operations = [
        migrations.RunPython(dedupe_view_events, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='proposalviewevent',
            constraint=models.UniqueConstraint(
                fields=['proposal', 'session_id'],
                name='uniq_proposalviewevent_proposal_session',
            ),
        ),
        migrations.AddIndex(
            model_name='proposalviewevent',
            index=models.Index(
                fields=['proposal', 'viewed_at'],
                name='content_pro_proposa_a6dbe7_idx',
            ),
        ),
        migrations.AddConstraint(
            model_name='diagnosticviewevent',
            constraint=models.UniqueConstraint(
                fields=['diagnostic', 'session_id'],
                name='uniq_diagnosticviewevent_diagnostic_session',
            ),
        ),
        migrations.AddIndex(
            model_name='diagnosticviewevent',
            index=models.Index(
                fields=['diagnostic', 'viewed_at'],
                name='content_dia_diagnos_6d810c_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='proposalsectionview',
            index=models.Index(
                fields=['view_event', 'section_type'],
                name='content_pro_view_ev_8e0901_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='diagnosticsectionview',
            index=models.Index(
                fields=['view_event', 'section_type'],
                name='content_dia_view_ev_2abe7d_idx',
            ),
        ),
    ]
