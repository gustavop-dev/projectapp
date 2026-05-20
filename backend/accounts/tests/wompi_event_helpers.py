"""Helpers to build Wompi webhook events with a valid signature for tests.

The webhook endpoint validates the event signature per Wompi's spec
(SHA256 of the concatenated signature.properties values + timestamp + events
secret). Tests must therefore post properly-signed events.
"""
import hashlib

from django.conf import settings

# The data paths whose values feed the checksum. Wompi may vary these per
# event; for tests a fixed realistic set is fine since the verifier reads the
# `properties` list back from the event we build here.
EVENT_PROPERTIES = ['transaction.id', 'transaction.status', 'transaction.amount_in_cents']


def signed_transaction_event(transaction, event='transaction.updated', timestamp=1700000000):
    """Build a Wompi event dict with a valid signature for `transaction` data."""
    data = {'transaction': transaction}

    parts = []
    for path in EVENT_PROPERTIES:
        value = data
        for key in path.split('.'):
            value = value.get(key) if isinstance(value, dict) else None
        parts.append('' if value is None else str(value))

    raw = ''.join(parts) + str(timestamp) + settings.WOMPI_EVENTS_SECRET
    checksum = hashlib.sha256(raw.encode()).hexdigest()

    return {
        'event': event,
        'data': data,
        'sent_at': '2026-05-20T00:00:00.000Z',
        'timestamp': timestamp,
        'signature': {
            'properties': EVENT_PROPERTIES,
            'checksum': checksum,
            'timestamp': timestamp,
        },
    }
