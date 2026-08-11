from django.db import models


class DocumentPaymentMethod(models.Model):
    """Structured payment instructions for a document."""

    # Labels in Spanish: they are printed verbatim on the cuenta de cobro PDF
    # and email, which are client-facing Spanish documents.
    class MethodType(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Transferencia bancaria'
        NEQUI = 'nequi', 'Nequi'
        DAVIPLATA = 'daviplata', 'Daviplata'
        WOMPI = 'wompi', 'Wompi'
        CASH = 'cash', 'Efectivo'
        OTHER = 'other', 'Otro'

    document = models.ForeignKey(
        'content.Document',
        on_delete=models.CASCADE,
        related_name='payment_methods',
    )
    payment_method_type = models.CharField(
        max_length=32,
        choices=MethodType.choices,
        default=MethodType.BANK_TRANSFER,
    )
    bank_name = models.CharField(max_length=128, blank=True, default='')
    account_type = models.CharField(max_length=32, blank=True, default='')
    account_number = models.CharField(max_length=64, blank=True, default='')
    account_holder_name = models.CharField(max_length=255, blank=True, default='')
    account_holder_identification = models.CharField(max_length=64, blank=True, default='')
    payment_instructions = models.TextField(blank=True, default='')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', 'id']

    def __str__(self):
        return f'PaymentMethod doc={self.document_id} {self.payment_method_type}'
