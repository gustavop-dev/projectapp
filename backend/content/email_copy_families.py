"""Stable families used to segment copies of every outbound email."""

PROPOSALS = 'proposals'
DIAGNOSTICS = 'diagnostics'
DOCUMENTS_COMMUNICATIONS = 'documents_communications'
COLLECTIONS = 'collections'
ACCOUNTING = 'accounting'
PLATFORM = 'platform'
TASKS_OPERATIONS = 'tasks_operations'
SECURITY = 'security'

# Compatibility name used by the client-only inventory introduced in 0209.
DOCUMENTS_MANUAL = DOCUMENTS_COMMUNICATIONS

EMAIL_COPY_FAMILY_CHOICES = (
    (PROPOSALS, 'Propuestas'),
    (DIAGNOSTICS, 'Diagnósticos'),
    (DOCUMENTS_COMMUNICATIONS, 'Documentos y comunicaciones'),
    (COLLECTIONS, 'Cuentas de cobro'),
    (ACCOUNTING, 'Contabilidad'),
    (PLATFORM, 'Plataforma'),
    (TASKS_OPERATIONS, 'Tareas y operaciones'),
    (SECURITY, 'Seguridad y acceso'),
)

EMAIL_COPY_FAMILY_VALUES = tuple(
    value for value, _label in EMAIL_COPY_FAMILY_CHOICES
)

# Public compatibility aliases. The API path is intentionally unchanged.
CLIENT_EMAIL_FAMILY_CHOICES = EMAIL_COPY_FAMILY_CHOICES
CLIENT_EMAIL_FAMILY_VALUES = EMAIL_COPY_FAMILY_VALUES
