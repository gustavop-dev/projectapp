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
):
    """Write one ``EmailLog`` per recipient and return them.

    The rendered message is stored once and shared by the sibling rows. The
    body is kept on the failure path too: diagnosing a bounce needs to show
    what could not be delivered.
    """
    from content.models import EmailBody, EmailLog, EmailLogTarget

    body = None
    if html_body or text_body:
        body = EmailBody.objects.create(
            html=html_body or '', text=text_body or '',
        )

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

    return logs
