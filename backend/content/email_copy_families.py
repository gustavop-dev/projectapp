"""Stable families used to segment internal copies of client email."""

PROPOSALS = 'proposals'
DIAGNOSTICS = 'diagnostics'
DOCUMENTS_MANUAL = 'documents_manual'
COLLECTIONS = 'collections'
PLATFORM = 'platform'

CLIENT_EMAIL_FAMILY_CHOICES = (
    (PROPOSALS, 'Propuestas'),
    (DIAGNOSTICS, 'Diagnósticos'),
    (DOCUMENTS_MANUAL, 'Documentos y correos manuales'),
    (COLLECTIONS, 'Cuentas de cobro'),
    (PLATFORM, 'Plataforma'),
)

CLIENT_EMAIL_FAMILY_VALUES = tuple(
    value for value, _label in CLIENT_EMAIL_FAMILY_CHOICES
)

