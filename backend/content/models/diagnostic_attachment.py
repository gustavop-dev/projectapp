from django.db import models


class DiagnosticAttachment(models.Model):
    """Files attached to a WebAppDiagnostic for admin → client sharing.

    Distinct from ``DiagnosticDocument`` (markdown templates rendered into
    the public view). Attachments are arbitrary uploaded files (annexes,
    client-provided docs, auxiliary PDFs) that can be emailed via the
    "Enviar documentos" modal.
    """

    DOC_TYPE_AMENDMENT = 'amendment'
    DOC_TYPE_LEGAL_ANNEX = 'legal_annex'
    DOC_TYPE_CLIENT_DOCUMENT = 'client_document'
    DOC_TYPE_OTHER = 'other'

    DOC_TYPE_CHOICES = [
        (DOC_TYPE_AMENDMENT, 'Otrosí'),
        (DOC_TYPE_LEGAL_ANNEX, 'Anexo legal'),
        (DOC_TYPE_CLIENT_DOCUMENT, 'Documento del cliente'),
        (DOC_TYPE_OTHER, 'Otro'),
    ]

    diagnostic = models.ForeignKey(
        'content.WebAppDiagnostic',
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    document_type = models.CharField(
        max_length=30,
        choices=DOC_TYPE_CHOICES,
        default=DOC_TYPE_OTHER,
    )
    title = models.CharField(max_length=300)
    file = models.FileField(upload_to='diagnostic_attachments/%Y/%m/')
    custom_type_label = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Custom label when document_type is "other".',
    )
    uploaded_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='diagnostic_attachments_uploaded',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_document_type_display()} — {self.title}'
