import pytest
from content.models import Document

pytestmark = pytest.mark.django_db


def test_default_template_style_is_professional():
    doc = Document.objects.create(title='X')
    assert doc.template_style == 'professional'


def test_template_style_accepts_friendly():
    doc = Document.objects.create(title='Y', template_style='friendly')
    doc.refresh_from_db()
    assert doc.template_style == 'friendly'


def test_template_style_choices():
    assert Document.TemplateStyle.FRIENDLY == 'friendly'
    assert Document.TemplateStyle.PROFESSIONAL == 'professional'
