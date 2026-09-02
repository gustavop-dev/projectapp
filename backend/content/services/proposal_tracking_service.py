"""Transactional persistence and commercial signals for proposal tracking."""

import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from content.models import (
    BusinessProposal,
    ProposalAlert,
    ProposalChangeLog,
    ProposalSectionView,
    ProposalViewEvent,
)
from content.services.proposal_analytics_service import (
    VIEW_MODE_LABELS,
    compute_heat_score_for_proposal,
)
from content.services.proposal_service import ProposalService

logger = logging.getLogger(__name__)


class ProposalTrackingService:
    """Own the write-side contract for one validated browser heartbeat."""

    @classmethod
    def record(cls, *, proposal_id, payload, ip_address, user_agent, referrer=''):
        now = timezone.now()
        with transaction.atomic():
            proposal = BusinessProposal.objects.select_for_update().get(pk=proposal_id)
            view_event, created = ProposalViewEvent.objects.get_or_create(
                proposal=proposal,
                session_id=payload['session_id'],
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'view_mode': payload['view_mode'],
                    'last_seen_at': now,
                },
            )

            first_view_confirmed = created and proposal.first_viewed_at is None
            event_update_fields = []
            if not created:
                view_event.last_seen_at = now
                event_update_fields.append('last_seen_at')
                if (
                    view_event.view_mode == 'unknown'
                    and payload['view_mode'] != 'unknown'
                ):
                    view_event.view_mode = payload['view_mode']
                    event_update_fields.append('view_mode')

            finalized_now = payload['is_final']
            if finalized_now:
                view_event.finalized_at = now
                event_update_fields.append('finalized_at')
            if event_update_fields:
                view_event.save(update_fields=event_update_fields)

            proposal_update_fields = ['last_activity_at']
            proposal.last_activity_at = now
            if created:
                proposal.view_count += 1
                proposal_update_fields.append('view_count')
                if first_view_confirmed:
                    proposal.first_viewed_at = now
                    proposal.first_view_notification_status = (
                        BusinessProposal.FirstViewNotificationStatus.PENDING
                    )
                    proposal.first_view_notification_attempts = 0
                    proposal.first_view_notification_attempted_at = None
                    proposal.first_view_notification_sent_at = None
                    proposal.first_view_notification_last_error = ''
                    proposal_update_fields.extend([
                        'first_viewed_at',
                        'first_view_notification_status',
                        'first_view_notification_attempts',
                        'first_view_notification_attempted_at',
                        'first_view_notification_sent_at',
                        'first_view_notification_last_error',
                    ])
                if proposal.status == BusinessProposal.Status.SENT:
                    proposal.status = BusinessProposal.Status.VIEWED
                    proposal_update_fields.append('status')
            proposal.save(update_fields=proposal_update_fields)

            if created:
                cls._record_view_activity(proposal, payload['view_mode'])
            if first_view_confirmed:
                ProposalAlert.objects.get_or_create(
                    proposal=proposal,
                    alert_type='first_view',
                    defaults={
                        'message': (
                            f'{proposal.client_name} confirmó la primera vista de '
                            f'"{proposal.title}".'
                        ),
                        'alert_date': now,
                    },
                )

            for section in payload['sections']:
                ProposalSectionView.objects.update_or_create(
                    view_event=view_event,
                    section_type=section['section_type'],
                    entered_at=section['entered_at'],
                    defaults={
                        'section_title': section['section_title'],
                        'subsection_key': section['subsection_key'],
                        'time_spent_seconds': section['time_spent_seconds'],
                        'view_mode': payload['view_mode'],
                    },
                )

            if finalized_now:
                cls._evaluate_engagement_decay(proposal, view_event, now)

        if created:
            cls._emit_session_signals(
                proposal,
                view_event,
                referrer=referrer,
                now=now,
            )
        cls._refresh_heat_score(proposal)
        return {
            'view_event_id': view_event.id,
            'created': created,
            'first_view_confirmed': first_view_confirmed,
            'finalized': view_event.finalized_at is not None,
        }

    @staticmethod
    def _record_view_activity(proposal, view_mode):
        mode_label = VIEW_MODE_LABELS.get(view_mode)
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type=ProposalChangeLog.ChangeType.VIEWED,
            actor_type=ProposalChangeLog.ActorType.CLIENT,
            description=(
                f'Vista en modo {mode_label}.'
                if mode_label
                else 'El cliente visitó la propuesta.'
            ),
        )

    @classmethod
    def _evaluate_engagement_decay(cls, proposal, current_event, now):
        if proposal.status not in (
            BusinessProposal.Status.SENT,
            BusinessProposal.Status.VIEWED,
        ):
            return

        current_count = current_event.section_views.count()
        previous_average = (
            ProposalViewEvent.objects
            .filter(proposal=proposal, finalized_at__isnull=False)
            .exclude(pk=current_event.pk)
            .annotate(section_count=Count('section_views'))
            .aggregate(value=Avg('section_count'))['value']
        )
        if previous_average is None or previous_average <= 0:
            return

        is_declining = current_count < previous_average * 0.5
        if proposal.engagement_declining != is_declining:
            proposal.engagement_declining = is_declining
            proposal.save(update_fields=['engagement_declining'])

        if not is_declining:
            return
        has_recent_alert = ProposalAlert.objects.filter(
            proposal=proposal,
            alert_type='engagement_decay',
            alert_date__gte=now - timedelta(days=3),
        ).exists()
        if not has_recent_alert:
            try:
                ProposalAlert.objects.create(
                    proposal=proposal,
                    alert_type='engagement_decay',
                    message=(
                        f'{proposal.client_name} vio {current_count} secciones '
                        f'vs promedio anterior de {previous_average:.0f}. '
                        'Posible pérdida de interés.'
                    ),
                    alert_date=now,
                )
            except Exception:
                logger.exception(
                    'Failed to create engagement_decay alert for %s',
                    proposal.uuid,
                )

    @classmethod
    def _emit_session_signals(cls, proposal, view_event, *, referrer, now):
        cls._emit_expired_or_rejected_signal(
            proposal,
            referrer=referrer,
            now=now,
        )
        if ProposalService.open_notifications_suppressed(proposal):
            return

        known_ips = set(
            ProposalViewEvent.objects
            .filter(proposal=proposal)
            .exclude(pk=view_event.pk)
            .exclude(ip_address__isnull=True)
            .exclude(ip_address='')
            .values_list('ip_address', flat=True)
        )
        if (
            not proposal.stakeholder_alert_sent_at
            and view_event.ip_address
            and known_ips
            and view_event.ip_address not in known_ips
        ):
            try:
                from content.services.proposal_email_service import ProposalEmailService

                sent = ProposalEmailService.send_stakeholder_detected_notification(
                    proposal,
                    len(known_ips) + 1,
                )
                if sent:
                    proposal.stakeholder_alert_sent_at = now
                    proposal.save(update_fields=['stakeholder_alert_sent_at'])
            except Exception:
                logger.exception(
                    'Failed to send stakeholder alert for proposal %s',
                    proposal.uuid,
                )

        cls._emit_revisit_signal(proposal, now)

    @staticmethod
    def _emit_expired_or_rejected_signal(proposal, *, referrer, now):
        from content.services.proposal_email_service import ProposalEmailService

        if (
            proposal.status == BusinessProposal.Status.EXPIRED
            and not proposal.post_expiration_alert_sent_at
        ):
            ProposalAlert.objects.get_or_create(
                proposal=proposal,
                alert_type='post_expiration_visit',
                defaults={
                    'message': (
                        f'{proposal.client_name} abrió la propuesta expirada '
                        f'"{proposal.title}". Señal de alto interés.'
                    ),
                    'alert_date': now,
                },
            )
            try:
                ProposalEmailService.send_post_expiration_visit_alert(proposal)
            except Exception:
                logger.exception(
                    'Failed to send post-expiration alert for proposal %s',
                    proposal.uuid,
                )
            proposal.post_expiration_alert_sent_at = now
            proposal.save(update_fields=['post_expiration_alert_sent_at'])

        rejection_is_old = (
            proposal.responded_at
            and proposal.responded_at + timedelta(days=7) < now
        )
        if (
            proposal.status == BusinessProposal.Status.REJECTED
            and referrer != 'reengagement'
            and rejection_is_old
        ):
            _, created = ProposalAlert.objects.get_or_create(
                proposal=proposal,
                alert_type='post_rejection_revisit',
                defaults={
                    'message': (
                        f'{proposal.client_name} revisitó la propuesta rechazada '
                        f'"{proposal.title}" después de 7+ días. '
                        'Posible reconsideración.'
                    ),
                    'alert_date': now,
                },
            )
            if created:
                try:
                    ProposalEmailService.send_post_rejection_revisit_alert(proposal)
                except Exception:
                    logger.exception(
                        'Failed to send post-rejection revisit alert for %s',
                        proposal.uuid,
                    )

    @staticmethod
    def _emit_revisit_signal(proposal, now):
        if (
            proposal.revisit_alert_sent_at
            or proposal.status not in (
                BusinessProposal.Status.SENT,
                BusinessProposal.Status.VIEWED,
            )
        ):
            return
        events = ProposalViewEvent.objects.filter(proposal=proposal)
        unique_sessions = events.values('session_id').distinct().count()
        latest_event_at = events.order_by('-viewed_at').values_list(
            'viewed_at', flat=True,
        ).first()
        if not (
            unique_sessions >= 3
            and proposal.first_viewed_at
            and latest_event_at
            and latest_event_at - proposal.first_viewed_at >= timedelta(days=3)
        ):
            return

        top = (
            ProposalSectionView.objects
            .filter(view_event__proposal=proposal)
            .values('section_type', 'section_title')
            .annotate(total_time=Sum('time_spent_seconds'))
            .order_by('-total_time')
            .first()
        )
        try:
            from content.services.proposal_email_service import ProposalEmailService

            sent = ProposalEmailService.send_revisit_alert(
                proposal,
                unique_sessions,
                top['section_title'] if top else '',
                top['total_time'] if top else 0,
            )
            if sent:
                proposal.revisit_alert_sent_at = now
                proposal.save(update_fields=['revisit_alert_sent_at'])
        except Exception:
            logger.exception(
                'Failed to send revisit alert for proposal %s',
                proposal.uuid,
            )

    @staticmethod
    def _refresh_heat_score(proposal):
        try:
            new_score = compute_heat_score_for_proposal(proposal.id, timezone.now())
            if new_score != proposal.cached_heat_score:
                BusinessProposal.objects.filter(pk=proposal.pk).update(
                    cached_heat_score=new_score,
                )
        except Exception:
            logger.exception(
                'Failed to update cached_heat_score for proposal %s',
                proposal.uuid,
            )
