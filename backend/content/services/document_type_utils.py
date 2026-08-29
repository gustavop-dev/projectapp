from content.models import DocumentType
from content.services.document_type_codes import (
    COLLECTION_ACCOUNT,
    COMMERCIAL_PROPOSAL,
    MARKDOWN,
)


def get_markdown_document_type():
    return DocumentType.objects.get(code=MARKDOWN)


def get_collection_account_document_type():
    return DocumentType.objects.get(code=COLLECTION_ACCOUNT)


def get_commercial_proposal_document_type():
    return DocumentType.objects.get(code=COMMERCIAL_PROPOSAL)
