"""Single writer for the log rows an automated send leaves behind.

Every notice of the accounting module reaches N recipients and produces N
``EmailLog`` rows, so each service used to repeat the same
``for recipient: EmailLog.objects.create(...)`` block twice — once for the
failure path and once for the success one. Worse, the record the notice was
about survived only inside a free-form ``metadata`` dict, which the history
could not query: asking "what went out for this hosting" meant reading JSON
by eye.

``record_send`` writes the rows, the shared body and the ``EmailLogTarget``
links in one place. The digest notices name several records at once, which
is why the links are their own rows instead of a column pair on the log.
"""

from django.db import transaction


def client_for_entity(entity_type, object_id):
    """Client pk behind a target row, or None.

    The write-time twin of ``accounting_history_service._client_target_q``,
    which resolves the same three entities at query time. Keep both in step:
    incomes and hostings point at the ``UserProfile``, a cuenta de cobro at
    the ``User`` behind it.
    """
    from content.models import Document, HostingRecord, IncomeRecord

    if not object_id:
        return None
    if entity_type == 'income':
        return (
            IncomeRecord.objects.filter(pk=object_id)
            .values_list('client_id', flat=True).first()
        )
    if entity_type == 'hosting':
        return (
            HostingRecord.objects.filter(pk=object_id)
            .values_list('client_id', flat=True).first()
        )
    if entity_type == 'collection_account':
        return (
            Document.objects.filter(pk=object_id)
            .values_list('client_user__profile__id', flat=True).first()
        )
    return None


def client_for_payment(payment):
    """Client profile behind a platform payment, or None.

    Its own resolver because ``_client_target_q`` never learned to read
    ``payment`` targets: the hosting payment notice is the one accounting
    notice its client filter cannot reach today.
    """
    project = getattr(getattr(payment, 'subscription', None), 'project', None)
    return getattr(getattr(project, 'client', None), 'profile', None)


def _normalize_targets(targets):
    """Coerce the callers' shorthand into ``(entity_type, id, repr)`` rows.

    Accepts dicts or ``(entity_type, object_id[, object_repr])`` sequences,
    drops the incomplete ones and de-duplicates, so a service can hand over
    whatever its context already holds without pre-cleaning it.
    """
    seen = set()
    rows = []
    for item in targets or ():
        if isinstance(item, dict):
            entity_type = item.get('entity_type')
            object_id = item.get('object_id')
            object_repr = item.get('object_repr') or ''
        else:
            entity_type, object_id, *rest = item
            object_repr = rest[0] if rest else ''
        if not entity_type or not object_id:
            continue
        key = (entity_type, int(object_id))
        if key in seen:
            continue
        seen.add(key)
        rows.append((entity_type, int(object_id), str(object_repr)[:255]))
    return rows


@transaction.atomic
def record_send(
    *,
    template_key,
    recipients,
    subject,
    status,
    metadata=None,
    targets=(),
    origin_action='',
    error_message='',
    html_body='',
    text_body='',
    retry_of=None,
    proposal=None,
    client=None,
    audience=None,
    delivery_id=None,
    delivery_role=None,
):
    """Write one ``EmailLog`` per recipient and return them.

    The rendered message is stored once and shared by the sibling rows. The
    body is kept on the failure path too: diagnosing a bounce needs to show
    what could not be delivered.

    ``client`` accepts an instance or a bare pk, so a caller holding only
    ``proposal.client_id`` does not have to load the profile. ``audience``
    defaults to internal: a forgotten one leaves the row out of a client's
    contact count, which is the harmless direction to be wrong in.
    """
    from content.models import EmailBody, EmailLog, EmailLogTarget
    from content.services.email_delivery_service import (
        complete_delivery_log_write,
        DeliveryClassification,
        matching_delivery_trace,
    )

    client_id = getattr(client, 'pk', client)
    audience = audience or EmailLog.Audience.INTERNAL
    delivery_role = delivery_role or EmailLog.DeliveryRole.PRIMARY
    trace = None
    if delivery_role == EmailLog.DeliveryRole.PRIMARY:
        trace = matching_delivery_trace(template_key, recipients)
    if trace is not None:
        delivery_id = delivery_id or trace.delivery_id

    body = trace.body if trace is not None else None
    if body is None and (html_body or text_body):
        body = EmailBody.objects.create(
            html=html_body or '', text=text_body or '',
        )
    if trace is not None and body is not None:
        trace.body = body

    logs = [
        EmailLog.objects.create(
            template_key=template_key,
            recipient=recipient,
            subject=subject,
            status=status,
            error_message=error_message or '',
            metadata=metadata or {},
            body=body,
            origin_action=origin_action or '',
            retry_of=retry_of,
            proposal=proposal,
            client_id=client_id,
            audience=audience,
            delivery_id=delivery_id,
            delivery_role=delivery_role,
        )
        for recipient in recipients
    ]

    rows = _normalize_targets(targets)
    if rows:
        EmailLogTarget.objects.bulk_create([
            EmailLogTarget(
                email_log=log,
                entity_type=entity_type,
                object_id=object_id,
                object_repr=object_repr,
            )
            for log in logs
            for entity_type, object_id, object_repr in rows
        ])

    # The gateway deliberately does not write history before the primary
    # caller has recorded its own result. Folding copy attempts in here gives
    # primary and copies one body, target set and delivery id, and avoids a
    # second logging dialect in every sender.
    if (
        trace is not None
        and trace.classification == DeliveryClassification.CLIENT
        and not trace.copies_recorded
    ):
        copy_logs = []
        for attempt in trace.copy_attempts:
            copy_metadata = dict(metadata or {})
            copy_metadata['client_email_copy'] = {
                'family': trace.family,
                'primary_recipients': list(trace.primary_recipients),
                'attempted_at': attempt.attempted_at,
            }
            copy_logs.append(EmailLog.objects.create(
                template_key=template_key,
                recipient=attempt.recipient,
                subject=subject,
                status=attempt.status,
                error_message=attempt.error_message,
                metadata=copy_metadata,
                body=body,
                origin_action=origin_action or '',
                retry_of=None,
                proposal=proposal,
                client_id=client_id,
                audience=EmailLog.Audience.INTERNAL,
                delivery_id=trace.delivery_id,
                delivery_role=EmailLog.DeliveryRole.COPY,
            ))
        if rows and copy_logs:
            EmailLogTarget.objects.bulk_create([
                EmailLogTarget(
                    email_log=log,
                    entity_type=entity_type,
                    object_id=object_id,
                    object_repr=object_repr,
                )
                for log in copy_logs
                for entity_type, object_id, object_repr in rows
            ])
        trace.copies_recorded = True

    if trace is not None:
        complete_delivery_log_write(trace)

    return logs


def attach_delivery_copies(logs):
    """Batch-load copy attempts and attach them to primary log instances."""
    from content.models import EmailLog

    logs = list(logs)
    delivery_ids = {
        log.delivery_id for log in logs
        if log.delivery_id and log.delivery_role == EmailLog.DeliveryRole.PRIMARY
    }
    copies_by_delivery = {delivery_id: [] for delivery_id in delivery_ids}
    if delivery_ids:
        copies = EmailLog.objects.filter(
            delivery_id__in=delivery_ids,
            delivery_role=EmailLog.DeliveryRole.COPY,
        ).order_by('sent_at', 'id')
        for copy_log in copies:
            copies_by_delivery.setdefault(copy_log.delivery_id, []).append(copy_log)
    for log in logs:
        log._delivery_copies = copies_by_delivery.get(log.delivery_id, [])
    return logs


def delivery_copy_payloads(log):
    """Serialize the internal attempts belonging to one primary delivery."""
    from content.models import EmailLog

    copies = getattr(log, '_delivery_copies', None)
    if copies is None:
        if not log.delivery_id or log.delivery_role != EmailLog.DeliveryRole.PRIMARY:
            copies = []
        else:
            copies = EmailLog.objects.filter(
                delivery_id=log.delivery_id,
                delivery_role=EmailLog.DeliveryRole.COPY,
            ).order_by('sent_at', 'id')
    return [
        {
            'id': copy_log.pk,
            'recipient': copy_log.recipient,
            'status': copy_log.status,
            'status_label': copy_log.get_status_display(),
            'error_message': copy_log.error_message,
            'sent_at': copy_log.sent_at,
        }
        for copy_log in copies
    ]
