"""Compatibility imports for migrations and integrations predating 0213."""

from .email_copy_recipient import (
    EmailCopyRecipient,
    default_email_copy_families,
)

ClientEmailCopyRecipient = EmailCopyRecipient
default_client_email_families = default_email_copy_families
