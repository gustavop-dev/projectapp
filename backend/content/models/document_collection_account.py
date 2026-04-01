from django.db import models


class DocumentCollectionAccount(models.Model):
    """1:1 extension for collection_account document type; stores snapshots at issue time."""

    class PaymentTermType(models.TextChoices):
        AGAINST_DELIVERY = 'against_delivery', 'Against delivery'
        FIXED_DATE = 'fixed_date', 'Fixed date'
        DAYS_AFTER_ISSUE = 'days_after_issue', 'Days after issue'

    document = models.OneToOneField(
        'content.Document',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='collection_account',
    )
    billing_concept = models.CharField(max_length=512, blank=True, default='')
    payment_term_type = models.CharField(
        max_length=32,
        choices=PaymentTermType.choices,
        default=PaymentTermType.DAYS_AFTER_ISSUE,
    )
    payment_term_days = models.PositiveIntegerField(null=True, blank=True)

    payer_name = models.CharField(max_length=255, blank=True, default='')
    payer_identification = models.CharField(max_length=64, blank=True, default='')
    payer_identification_type = models.CharField(max_length=32, blank=True, default='')
    payer_address = models.CharField(max_length=512, blank=True, default='')
    payer_phone = models.CharField(max_length=64, blank=True, default='')
    payer_email = models.EmailField(blank=True, default='')

    customer_name = models.CharField(max_length=255, blank=True, default='')
    customer_identification = models.CharField(max_length=64, blank=True, default='')
    customer_identification_type = models.CharField(max_length=32, blank=True, default='')
    customer_contact_name = models.CharField(max_length=255, blank=True, default='')
    customer_email = models.EmailField(blank=True, default='')
    customer_address = models.CharField(max_length=512, blank=True, default='')

    observations = models.TextField(blank=True, default='')
    support_reference = models.CharField(max_length=512, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'CollectionAccount doc={self.document_id}'
