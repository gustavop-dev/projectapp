"""
Huey tasks for the business proposal feature.

Tasks:
  - send_proposal_reminder: Send reminder email N days after proposal was sent.
  - expire_stale_proposals: Daily task to mark expired proposals.
"""

import logging
from datetime import timedelta

from django.utils import timezone
from huey import crontab
from huey.contrib.djhuey import periodic_task, task

logger = logging.getLogger(__name__)


@task()
def send_proposal_reminder(proposal_id):
    """
    Huey task: send reminder email N days after proposal was sent.

    Skips if:
    - Proposal not found
    - Status is not SENT or VIEWED
    - No client_email set
    - Reminder already sent (reminder_sent_at is not null)
    """
    from content.models import BusinessProposal
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning('Proposal %s not found for reminder task.', proposal_id)
        return

    if proposal.automations_paused:
        logger.info(
            'Skipping reminder for proposal %s: automations paused',
            proposal.uuid,
        )
        return

    if proposal.status not in ('sent', 'viewed'):
        logger.info(
            'Skipping reminder for proposal %s: status is %s',
            proposal.uuid, proposal.status,
        )
        return

    if not proposal.client_email:
        logger.warning(
            'Skipping reminder for proposal %s: no client_email',
            proposal.uuid,
        )
        return

    if proposal.reminder_sent_at is not None:
        logger.info(
            'Skipping reminder for proposal %s: already sent at %s',
            proposal.uuid, proposal.reminder_sent_at,
        )
        return

    ProposalEmailService.send_reminder(proposal)


@task()
def send_urgency_reminder(proposal_id):
    """
    Huey task: send urgency/discount email at day 15 after proposal was sent.

    Skips if:
    - Proposal not found
    - Status is not SENT or VIEWED
    - No client_email set
    - Urgency email already sent (urgency_email_sent_at is not null)
    """
    from content.models import BusinessProposal
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning('Proposal %s not found for urgency task.', proposal_id)
        return

    if proposal.automations_paused:
        logger.info(
            'Skipping urgency for proposal %s: automations paused',
            proposal.uuid,
        )
        return

    if proposal.status not in ('sent', 'viewed'):
        logger.info(
            'Skipping urgency for proposal %s: status is %s',
            proposal.uuid, proposal.status,
        )
        return

    if not proposal.client_email:
        logger.warning(
            'Skipping urgency for proposal %s: no client_email',
            proposal.uuid,
        )
        return

    if proposal.urgency_email_sent_at is not None:
        logger.info(
            'Skipping urgency for proposal %s: already sent at %s',
            proposal.uuid, proposal.urgency_email_sent_at,
        )
        return

    ProposalEmailService.send_urgency_email(proposal)


@task()
def send_rejection_reengagement(proposal_id):
    """
    Huey task: send re-engagement email 48h after a budget-related rejection.

    Skips if:
    - Proposal not found
    - Status is not REJECTED
    - No client_email set
    - Re-engagement email already sent (ProposalChangeLog entry exists)
    """
    from content.models import BusinessProposal, ProposalChangeLog
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning(
            'Proposal %s not found for re-engagement task.', proposal_id
        )
        return

    if proposal.status != 'rejected':
        logger.info(
            'Skipping re-engagement for proposal %s: status is %s',
            proposal.uuid, proposal.status,
        )
        return

    if not proposal.client_email:
        logger.warning(
            'Skipping re-engagement for proposal %s: no client_email',
            proposal.uuid,
        )
        return

    already_sent = ProposalChangeLog.objects.filter(
        proposal=proposal,
        change_type='reengagement',
    ).exists()
    if already_sent:
        logger.info(
            'Skipping re-engagement for proposal %s: already sent',
            proposal.uuid,
        )
        return

    success = ProposalEmailService.send_rejection_reengagement(proposal)
    if success:
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='reengagement',
            actor_type='system',
            description='Re-engagement email sent 48h after budget rejection.',
        )


@periodic_task(crontab(hour='8', minute='0'))
def suggest_pre_expiration_discount():
    """
    Daily task: for proposals expiring within 5 days that were viewed but
    not responded and have no discount, create a discount_suggestion alert
    (if one doesn't already exist).
    """
    from datetime import timedelta

    from content.models import BusinessProposal, ProposalAlert

    now = timezone.now()
    candidates = BusinessProposal.objects.filter(
        status='viewed',
        is_active=True,
        discount_percent=0,
        responded_at__isnull=True,
        expires_at__isnull=False,
        expires_at__gt=now,
        expires_at__lte=now + timedelta(days=5),
    )

    created_count = 0
    for proposal in candidates:
        already_exists = ProposalAlert.objects.filter(
            proposal=proposal,
            alert_type='discount_suggestion',
            is_dismissed=False,
        ).exists()
        if not already_exists:
            days_left = (proposal.expires_at - now).days
            ProposalAlert.objects.create(
                proposal=proposal,
                alert_type='discount_suggestion',
                message=(
                    f'Expira en {days_left}d, vista pero sin respuesta. '
                    f'Considera activar descuento o re-enviar con nota personalizada.'
                ),
                alert_date=now,
            )
            created_count += 1

    if created_count > 0:
        logger.info(
            'Created %d pre-expiration discount suggestions.', created_count
        )


@periodic_task(crontab(hour='0', minute='30'))
def expire_stale_proposals():
    """
    Daily task: mark proposals as EXPIRED when expires_at < now().

    Only affects active proposals with status SENT or VIEWED.
    Auto-extends by 7 days if the client had recent activity (last 3 days).
    """
    from content.models import BusinessProposal, ProposalChangeLog
    from content.models import ProposalViewEvent

    now = timezone.now()
    candidates = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed'],
        is_active=True,
        expires_at__lt=now,
    )

    expired = 0
    extended = 0
    for proposal in candidates:
        # Check for recent client activity (view event in last 3 days)
        recent_activity = ProposalViewEvent.objects.filter(
            proposal=proposal,
            viewed_at__gte=now - timedelta(days=3),
        ).exists()

        if recent_activity:
            # Auto-extend by 7 days
            proposal.expires_at = now + timedelta(days=7)
            proposal.save(update_fields=['expires_at'])
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='updated',
                actor_type='system',
                description=(
                    'Auto-extended expiration by 7 days due to recent client activity.'
                ),
            )
            extended += 1
        else:
            proposal.status = 'expired'
            proposal.save(update_fields=['status'])
            expired += 1

    if expired > 0:
        logger.info('Expired %d stale proposals.', expired)
    if extended > 0:
        logger.info('Auto-extended %d proposals with recent activity.', extended)


@periodic_task(crontab(hour='9', minute='0'))
def escalate_seller_inactivity():
    """
    Daily task: if a proposal has had no seller activity for >=5 days
    (sent/viewed, client has viewed), send an escalation email to the
    sales team. Only sends once per proposal (tracked via ProposalChangeLog).
    """
    from datetime import timedelta

    from content.models import BusinessProposal, ProposalChangeLog
    from content.services.proposal_email_service import ProposalEmailService

    now = timezone.now()
    five_days_ago = now - timedelta(days=5)
    seller_activity_types = {'call', 'meeting', 'followup', 'note'}

    candidates = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed'],
        is_active=True,
        automations_paused=False,
        first_viewed_at__isnull=False,
    )

    escalated = 0
    for p in candidates:
        ref_date = p.last_activity_at or p.sent_at
        if not ref_date or ref_date > five_days_ago:
            continue

        has_recent = ProposalChangeLog.objects.filter(
            proposal=p,
            change_type__in=seller_activity_types,
            created_at__gte=five_days_ago,
        ).exists()
        if has_recent:
            continue

        already_escalated = ProposalChangeLog.objects.filter(
            proposal=p,
            change_type=ProposalChangeLog.ChangeType.SELLER_INACTIVITY_ESCALATION,
        ).exists()
        if already_escalated:
            continue

        days = (now - ref_date).days
        try:
            ProposalEmailService.send_seller_inactivity_escalation(p, days)
            ProposalChangeLog.objects.create(
                proposal=p,
                change_type=ProposalChangeLog.ChangeType.SELLER_INACTIVITY_ESCALATION,
                actor_type='system',
                description=f'Seller inactivity escalation sent after {days} days.',
            )
            escalated += 1
        except Exception:
            logger.exception(
                'Failed seller inactivity escalation for proposal %s',
                p.uuid,
            )

    if escalated > 0:
        logger.info('Escalated %d seller-inactive proposals.', escalated)


@periodic_task(crontab(hour='*/2', minute='15'))
def check_engagement_followups():
    """
    Periodic task (every 2 hours): check viewed proposals for
    engagement-based follow-up email triggers.

    1. Abandonment: client viewed but never reached investment section,
       and first view was >4h ago.
    2. Investment interest: client spent >60s on investment section,
       and last view was >2h ago.
    """
    from datetime import timedelta

    from django.db.models import Sum

    from content.models import (
        BusinessProposal, ProposalSectionView, ProposalViewEvent,
    )
    from content.services.proposal_email_service import ProposalEmailService

    now = timezone.now()
    four_hours_ago = now - timedelta(hours=4)
    two_hours_ago = now - timedelta(hours=2)

    # --- Abandonment follow-up ---
    abandonment_candidates = BusinessProposal.objects.filter(
        status='viewed',
        is_active=True,
        automations_paused=False,
        client_email__gt='',
        abandonment_email_sent_at__isnull=True,
        first_viewed_at__isnull=False,
        first_viewed_at__lt=four_hours_ago,
    )

    for proposal in abandonment_candidates:
        visited_types = set(
            ProposalSectionView.objects
            .filter(view_event__proposal=proposal)
            .values_list('section_type', flat=True)
            .distinct()
        )
        if 'investment' not in visited_types:
            try:
                ProposalEmailService.send_abandonment_followup(proposal)
                logger.info(
                    'Sent abandonment followup for proposal %s',
                    proposal.uuid,
                )
            except Exception:
                logger.exception(
                    'Failed abandonment followup for proposal %s',
                    proposal.uuid,
                )

    # --- Investment interest follow-up ---
    interest_candidates = BusinessProposal.objects.filter(
        status='viewed',
        is_active=True,
        automations_paused=False,
        client_email__gt='',
        investment_interest_email_sent_at__isnull=True,
        first_viewed_at__isnull=False,
    )

    for proposal in interest_candidates:
        last_event = (
            ProposalViewEvent.objects
            .filter(proposal=proposal)
            .order_by('-viewed_at')
            .first()
        )
        if not last_event or last_event.viewed_at > two_hours_ago:
            continue

        investment_time = (
            ProposalSectionView.objects
            .filter(
                view_event__proposal=proposal,
                section_type='investment',
            )
            .aggregate(total=Sum('time_spent_seconds'))
        )['total'] or 0

        if investment_time >= 60:
            try:
                ProposalEmailService.send_investment_interest_followup(
                    proposal, investment_time,
                )
                logger.info(
                    'Sent investment interest followup for proposal %s '
                    '(time=%ds)',
                    proposal.uuid, investment_time,
                )
            except Exception:
                logger.exception(
                    'Failed investment interest followup for proposal %s',
                    proposal.uuid,
                )


@task()
def send_scheduled_followup(proposal_id):
    """
    Huey task: send a scheduled follow-up email for a previously
    rejected proposal (client asked to be reminded later).

    Skips if:
    - Proposal not found
    - No client_email set
    - No followup_scheduled_at set
    """
    from content.models import BusinessProposal
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning(
            'Proposal %s not found for scheduled followup task.',
            proposal_id,
        )
        return

    if not proposal.client_email:
        logger.warning(
            'Skipping scheduled followup for proposal %s: no client_email',
            proposal.uuid,
        )
        return

    if not proposal.followup_scheduled_at:
        logger.info(
            'Skipping scheduled followup for proposal %s: no scheduled date',
            proposal.uuid,
        )
        return

    ProposalEmailService.send_scheduled_followup(proposal)


@periodic_task(crontab(minute='*/15'))
def publish_scheduled_blog_posts():
    """
    Periodic task (every 15 minutes): publish blog posts whose
    published_at datetime has passed but are still marked as drafts.

    This enables scheduled/future publishing from the admin panel.
    """
    from content.models import BlogPost

    now = timezone.now()
    scheduled_qs = BlogPost.objects.filter(
        is_published=False,
        published_at__isnull=False,
        published_at__lte=now,
    )
    count = scheduled_qs.update(is_published=True)

    if count > 0:
        logger.info('Published %d scheduled blog post(s).', count)


def _suggest_action_for_proposal(proposal, now):
    """
    Generate a contextual suggested action for a single proposal
    based on its current state, engagement signals, and timing.

    Returns a short actionable string for the daily digest email.
    """
    from datetime import timedelta

    # Negotiating → follow up on the negotiation
    if proposal.status == 'negotiating':
        return 'Seguir negociación: enviar opciones de ajuste o agendar llamada.'

    # High view count today-ish → call now
    if proposal.view_count and proposal.view_count >= 3:
        return f'Llamar hoy: {proposal.view_count} visitas registradas. Alta intención.'

    # Expiring soon → offer discount or extend
    if proposal.expires_at:
        days_left = (proposal.expires_at - now).days
        if 0 < days_left <= 3:
            if not proposal.discount_percent:
                return f'Expira en {days_left}d. Considerar activar descuento o re-enviar con nota.'
            return f'Expira en {days_left}d. Enviar recordatorio de urgencia.'

    # Viewed but no response → WhatsApp follow-up
    if proposal.status == 'viewed':
        ref_date = proposal.last_activity_at or proposal.first_viewed_at
        if ref_date and (now - ref_date) > timedelta(days=2):
            days_waiting = (now - ref_date).days
            return f'Sin respuesta hace {days_waiting}d. Enviar WhatsApp personalizado.'
        return 'Visto recientemente. Esperar 24-48h o enviar WhatsApp de refuerzo.'

    # Sent but never viewed → re-send or call
    if proposal.status == 'sent':
        if proposal.sent_at and (now - proposal.sent_at) > timedelta(days=3):
            return 'Sin abrir hace >3d. Re-enviar propuesta o contactar por teléfono.'
        return 'Enviada recientemente. Esperar a que la abra.'

    return 'Revisar estado y dar seguimiento.'


@periodic_task(crontab(hour='7', minute='0'))
def send_daily_pipeline_digest():
    """
    Daily task (7 AM): compile and send a pipeline digest email
    summarising: proposals viewed yesterday, inactive proposals,
    proposals expiring within 5 days, total active count, and
    a suggested action #1 per proposal.
    """
    from datetime import timedelta

    from content.models import BusinessProposal, ProposalViewEvent
    from content.services.proposal_email_service import ProposalEmailService
    from content.utils import format_bogota_date

    now = timezone.now()
    yesterday_start = (now - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    yesterday_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    three_days_ago = now - timedelta(days=3)

    active_proposals = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed', 'negotiating'],
        is_active=True,
    )

    # Proposals viewed yesterday
    viewed_yesterday_ids = (
        ProposalViewEvent.objects
        .filter(viewed_at__gte=yesterday_start, viewed_at__lt=yesterday_end)
        .values_list('proposal_id', flat=True)
        .distinct()
    )
    viewed_yesterday_qs = active_proposals.filter(pk__in=viewed_yesterday_ids)
    viewed_yesterday = []
    for p in viewed_yesterday_qs:
        viewed_yesterday.append({
            'id': p.id,
            'client_name': p.client_name,
            'title': p.title,
            'status': p.status,
            'total_investment': p.total_investment,
            'currency': p.currency,
            'suggested_action': _suggest_action_for_proposal(p, now),
        })

    # Inactive proposals (no activity >3 days)
    inactive = []
    for p in active_proposals.filter(status__in=['sent', 'viewed', 'negotiating']):
        ref_date = p.last_activity_at or p.sent_at
        if ref_date and ref_date < three_days_ago:
            inactive.append({
                'id': p.id,
                'client_name': p.client_name,
                'title': p.title,
                'days_inactive': (now - ref_date).days,
                'suggested_action': _suggest_action_for_proposal(p, now),
            })

    # Expiring within 5 days
    expiring_soon_qs = active_proposals.filter(
        expires_at__isnull=False,
        expires_at__gt=now,
        expires_at__lte=now + timedelta(days=5),
    )
    expiring_soon = []
    for p in expiring_soon_qs:
        expiring_soon.append({
            'id': p.id,
            'client_name': p.client_name,
            'title': p.title,
            'expires_at': p.expires_at,
            'suggested_action': _suggest_action_for_proposal(p, now),
        })

    digest_data = {
        'viewed_yesterday': viewed_yesterday,
        'inactive': inactive,
        'expiring_soon': expiring_soon,
        'total_active': active_proposals.count(),
        'date': format_bogota_date(now),
    }

    ProposalEmailService.send_daily_pipeline_digest(digest_data)


@periodic_task(crontab(hour='*/3', minute='45'))
def detect_high_engagement_today():
    """
    Periodic task (every 3 hours): if a client has >=3 unique view sessions
    on a proposal today, create a high_engagement_today alert for the seller.
    Rate-limited to one alert per day per proposal.
    """
    from datetime import timedelta

    from content.models import BusinessProposal, ProposalAlert, ProposalViewEvent

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    active_proposals = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed', 'negotiating'],
        is_active=True,
    )

    created = 0
    for proposal in active_proposals:
        sessions_today = (
            ProposalViewEvent.objects
            .filter(proposal=proposal, viewed_at__gte=today_start)
            .values('session_id')
            .distinct()
            .count()
        )
        if sessions_today < 3:
            continue

        already_alerted = ProposalAlert.objects.filter(
            proposal=proposal,
            alert_type='high_engagement_today',
            is_dismissed=False,
            created_at__gte=today_start,
        ).exists()
        if already_alerted:
            continue

        ProposalAlert.objects.create(
            proposal=proposal,
            alert_type='high_engagement_today',
            message=(
                f'{proposal.client_name} visitó la propuesta '
                f'{sessions_today} veces hoy. Considera llamar ahora.'
            ),
            alert_date=now,
        )
        created += 1

    if created > 0:
        logger.info('Created %d high-engagement alerts.', created)


@periodic_task(crontab(hour='*/2', minute='30'))
def check_calculator_abandonment_followup():
    """
    Periodic task (every 2 hours): if a client abandoned the calculator
    (calc_abandoned logged) >24h ago, with no subsequent calc_confirmed,
    proposal still viewed/sent, and no response — create follow-up alert.

    Enhanced: also detects high-intent sessions where the client spent >5min
    in the calculator before abandoning, and includes this in the alert message.
    """
    import json as _json
    from datetime import timedelta

    from content.models import BusinessProposal, ProposalAlert, ProposalChangeLog

    now = timezone.now()
    one_day_ago = now - timedelta(hours=24)

    candidates = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed'],
        is_active=True,
        automations_paused=False,
        calculator_followup_sent_at__isnull=True,
        responded_at__isnull=True,
    )

    created = 0
    for proposal in candidates:
        abandoned_logs = ProposalChangeLog.objects.filter(
            proposal=proposal,
            change_type='calc_abandoned',
            created_at__lt=one_day_ago,
        ).order_by('-created_at')
        if not abandoned_logs.exists():
            continue

        has_confirmed_after = ProposalChangeLog.objects.filter(
            proposal=proposal,
            change_type='calc_confirmed',
            created_at__gt=one_day_ago,
        ).exists()
        if has_confirmed_after:
            continue

        # Check elapsed time from the most recent abandonment event
        max_elapsed = 0
        latest_log = abandoned_logs.first()
        if latest_log and latest_log.description:
            try:
                data = _json.loads(latest_log.description)
                max_elapsed = data.get('elapsed_seconds', 0)
            except (ValueError, TypeError):
                pass

        high_intent = max_elapsed >= 300  # >5 minutes
        if high_intent:
            minutes = max_elapsed // 60
            message = (
                f'{proposal.client_name} pasó {minutes}+ min en el calculador '
                f'sin confirmar (alta intención). Enviar: '
                f'"¿Tienes dudas sobre los módulos? Puedo ajustar la selección contigo."'
            )
        else:
            message = (
                f'{proposal.client_name} abandonó el calculador hace >24h '
                f'sin confirmar. Considera enviar seguimiento.'
            )

        ProposalAlert.objects.create(
            proposal=proposal,
            alert_type='calculator_followup',
            message=message,
            alert_date=now,
        )
        proposal.calculator_followup_sent_at = now
        proposal.save(update_fields=['calculator_followup_sent_at'])
        created += 1

    if created > 0:
        logger.info('Created %d calculator followup alerts.', created)


@periodic_task(crontab(hour='9', minute='30'))
def generate_whatsapp_suggestions():
    """
    Daily task (9:30 AM): for proposals viewed >48h ago without response,
    generate a WhatsApp suggestion alert with a pre-drafted message
    mentioning the section where the client spent most time.
    """
    from datetime import timedelta

    from django.db.models import Sum

    from content.models import (
        BusinessProposal, ProposalAlert, ProposalSectionView,
    )

    now = timezone.now()
    two_days_ago = now - timedelta(hours=48)

    candidates = BusinessProposal.objects.filter(
        status='viewed',
        is_active=True,
        automations_paused=False,
        responded_at__isnull=True,
        first_viewed_at__isnull=False,
        first_viewed_at__lt=two_days_ago,
        client_phone__gt='',
    )

    created = 0
    for proposal in candidates:
        already_exists = ProposalAlert.objects.filter(
            proposal=proposal,
            alert_type='whatsapp_suggestion',
            is_dismissed=False,
        ).exists()
        if already_exists:
            continue

        top_section = (
            ProposalSectionView.objects
            .filter(view_event__proposal=proposal)
            .values('section_type')
            .annotate(total_time=Sum('time_spent_seconds'))
            .order_by('-total_time')
            .first()
        )

        section_name = (top_section['section_type'] if top_section else 'la propuesta')
        section_labels = {
            'greeting': 'bienvenida',
            'executive_summary': 'resumen ejecutivo',
            'context_diagnostic': 'diagnóstico y contexto',
            'conversion_strategy': 'estrategia de conversión',
            'design_ux': 'diseño y UX',
            'creative_support': 'soporte creativo',
            'development_stages': 'etapas de desarrollo',
            'functional_requirements': 'requerimientos funcionales',
            'timeline': 'cronograma',
            'investment': 'inversión',
            'final_note': 'nota final',
            'next_steps': 'próximos pasos',
            'proposal_summary': 'resumen',
            'process_methodology': 'proceso y metodología',
            'closing': 'cierre',
            'about_us': 'sobre nosotros',
        }
        label = section_labels.get(section_name, section_name)

        message_draft = (
            f'Hola {proposal.client_name}, vi que revisaste la sección de '
            f'{label} con mucho interés. ¿Te puedo ayudar con alguna duda?'
        )

        ProposalAlert.objects.create(
            proposal=proposal,
            alert_type='whatsapp_suggestion',
            message=f'Sugerencia de WhatsApp para {proposal.client_name}: "{message_draft}"',
            alert_date=now,
        )
        created += 1

    if created > 0:
        logger.info('Created %d WhatsApp suggestions.', created)


@periodic_task(crontab(hour='1', minute='30'))
def auto_archive_zombie_proposals():
    """
    Daily task: deactivate proposals that are expired and had no
    interaction (views or change logs) in the last 30 days.
    """
    from datetime import timedelta

    from django.db.models import Max

    from content.models import BusinessProposal, ProposalChangeLog

    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    candidates = BusinessProposal.objects.filter(
        status='expired',
        is_active=True,
    )

    archived = 0
    for proposal in candidates:
        last_view = (
            proposal.view_events
            .aggregate(latest=Max('viewed_at'))['latest']
        )
        last_log = (
            ProposalChangeLog.objects
            .filter(proposal=proposal)
            .aggregate(latest=Max('created_at'))['latest']
        )

        latest_activity = max(
            filter(None, [last_view, last_log, proposal.created_at])
        )
        if latest_activity and latest_activity < thirty_days_ago:
            proposal.is_active = False
            proposal.save(update_fields=['is_active'])
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='auto_archived',
                actor_type='system',
                description='Auto-archived: expired with no activity for 30+ days.',
            )
            archived += 1

    if archived > 0:
        logger.info('Auto-archived %d zombie proposals.', archived)


@periodic_task(crontab(minute='*/30'))
def refresh_cached_heat_scores():
    """
    Periodic task (every 30 min): recompute cached_heat_score for all
    active proposals in sent/viewed status.
    """
    from content.models import BusinessProposal
    from content.views.proposal import _compute_heat_score_for_proposal

    now = timezone.now()
    proposals = BusinessProposal.objects.filter(
        status__in=['sent', 'viewed'],
        is_active=True,
    ).values_list('id', 'cached_heat_score')

    updated = 0
    for pid, old_score in proposals:
        new_score = _compute_heat_score_for_proposal(pid, now)
        if new_score != old_score:
            BusinessProposal.objects.filter(pk=pid).update(
                cached_heat_score=new_score
            )
            updated += 1

    if updated > 0:
        logger.info('Refreshed cached_heat_score for %d proposals.', updated)


@task()
def notify_first_view(proposal_id):
    """
    Huey task: send real-time notification to the sales team when a
    client opens a proposal for the first time.

    Called asynchronously from retrieve_public_proposal so the client's
    page load is not blocked by email delivery.
    """
    from content.models import BusinessProposal
    from content.services.proposal_email_service import ProposalEmailService

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning(
            'Proposal %s not found for first-view notification task.',
            proposal_id,
        )
        return

    ProposalEmailService.send_first_view_notification(proposal)


@task()
def run_platform_onboarding(proposal_id, acting_user_id=None, is_relaunch=False):
    """
    Huey task: run platform onboarding for an accepted proposal.

    Creates project, deliverable, syncs requirements and documents,
    and sends acceptance email (first launch only). Wrapped in
    transaction.atomic() so partial failures roll back cleanly.

    Updates platform_onboarding_status to 'completed' or 'failed'.
    """
    from django.db import transaction

    from content.models import BusinessProposal

    try:
        proposal = BusinessProposal.objects.get(pk=proposal_id)
    except BusinessProposal.DoesNotExist:
        logger.warning(
            'Proposal %s not found for platform onboarding task.',
            proposal_id,
        )
        return

    acting_user = None
    if acting_user_id:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        acting_user = User.objects.filter(pk=acting_user_id).first()

    try:
        with transaction.atomic():
            from accounts.services.proposal_platform_onboarding import (
                handle_proposal_accepted_for_platform,
            )

            handle_proposal_accepted_for_platform(
                proposal,
                source='admin_panel',
                acting_user=acting_user,
                send_email=not is_relaunch,
            )

        proposal.platform_onboarding_status = BusinessProposal.ONBOARDING_COMPLETED
        proposal.save(update_fields=['platform_onboarding_status'])
    except Exception:
        logger.exception(
            'Platform onboarding failed for proposal %s.', proposal_id,
        )
        proposal.platform_onboarding_status = BusinessProposal.ONBOARDING_FAILED
        proposal.save(update_fields=['platform_onboarding_status'])
