"""Reusable, MIME-capable doubles for outbound email tests."""

from unittest.mock import MagicMock

from django.core.mail import EmailMultiAlternatives


def stub_email_message():
    """Return a mock that preserves assertions and can build a real MIME tree.

    ``EmailDeliveryGateway`` archives the exact MIME payload before sending it.
    Legacy tests still need a mock ``send`` method, but a bare ``MagicMock`` is
    not a valid email message. This double reconstructs the real message from
    the patched constructor call and replays attachments for snapshot capture.
    """
    email = MagicMock()
    email.subject = ''
    email.body = ''
    email.from_email = ''
    email.to = []
    email.cc = []
    email.bcc = []
    email.alternatives = []
    email.send.return_value = 1
    constructor_args = None
    constructor_kwargs = None

    def real_message():
        nonlocal constructor_args, constructor_kwargs
        if constructor_args is not None:
            return EmailMultiAlternatives(
                *constructor_args,
                **constructor_kwargs,
            )
        constructor = getattr(email, '_mock_new_parent', None)
        call = getattr(constructor, 'call_args', None)
        if call is None:
            return EmailMultiAlternatives(
                subject=email.subject,
                body=email.body,
                from_email=email.from_email,
                to=list(email.to),
                cc=list(email.cc),
                bcc=list(email.bcc),
            )
        constructor_args = tuple(call.args)
        constructor_kwargs = dict(call.kwargs)
        return EmailMultiAlternatives(
            *constructor_args,
            **constructor_kwargs,
        )

    def sync_headers():
        message = real_message()
        email.subject = message.subject
        email.body = message.body
        email.from_email = message.from_email
        email.to = list(message.to or [])
        email.cc = list(message.cc or [])
        email.bcc = list(message.bcc or [])
        return message

    def attach_alternative(content, mimetype):
        email.alternatives = [
            *email.alternatives,
            (content, mimetype),
        ]

    def recipients():
        message = sync_headers()
        # ``patch(...).return_value = email`` parents MagicMocks to the
        # constructor. Retaining that entire graph makes gateway deepcopy
        # needlessly expensive; the constructor arguments above are enough.
        email._mock_new_parent = None
        return message.recipients()

    def mime_message():
        message = sync_headers()
        for call in email.attach_alternative.call_args_list:
            message.attach_alternative(*call.args, **call.kwargs)
        for call in email.attach.call_args_list:
            message.attach(*call.args, **call.kwargs)
        return message.message()

    email.attach_alternative.side_effect = attach_alternative
    email.recipients.side_effect = recipients
    email.message.side_effect = mime_message
    return email
