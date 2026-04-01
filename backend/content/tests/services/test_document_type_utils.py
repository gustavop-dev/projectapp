"""Tests for document_type_utils helpers."""

import pytest

from content.services.document_type_codes import COLLECTION_ACCOUNT, MARKDOWN
from content.services.document_type_utils import (
    get_collection_account_document_type,
    get_markdown_document_type,
)

pytestmark = pytest.mark.django_db


def test_get_markdown_document_type_returns_type_with_markdown_code():
    dt = get_markdown_document_type()

    assert dt.code == MARKDOWN


def test_get_collection_account_document_type_returns_type_with_collection_code():
    dt = get_collection_account_document_type()

    assert dt.code == COLLECTION_ACCOUNT
