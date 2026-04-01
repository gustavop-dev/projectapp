"""Append-only payment status transition log."""

from accounts.models import PaymentHistory


def record_payment_status_change(payment, old_status, new_status, source='', metadata=None):
    """
    Persist a PaymentHistory row when status actually changes.
    Call after updating in-memory payment.status but typically before or after save;
    payment.pk must exist.
    """
    if old_status == new_status:
        return None
    return PaymentHistory.objects.create(
        payment=payment,
        from_status=old_status,
        to_status=new_status,
        source=source or '',
        metadata=metadata if metadata is not None else {},
    )
