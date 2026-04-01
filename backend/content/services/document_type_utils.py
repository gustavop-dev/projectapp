from content.models import DocumentType
from content.services.document_type_codes import COLLECTION_ACCOUNT, MARKDOWN


def get_markdown_document_type():
    return DocumentType.objects.get(code=MARKDOWN)


def get_collection_account_document_type():
    return DocumentType.objects.get(code=COLLECTION_ACCOUNT)
