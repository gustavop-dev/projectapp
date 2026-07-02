"""Tests for the `create_estimate_document` management command.

Business rules asserted:
- Creates a markdown Document inside the requested top-level folder
- The folder is created once (get_or_create) and reused on later runs
- Content, status and language land on the created Document
- A missing or empty markdown file aborts with CommandError
- Title collisions version (" — vN") by default, or update in place with
  --on-conflict replace
- Output always includes the direct panel URL
"""
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from content.models import Document, DocumentFolder
from content.services.document_type_codes import MARKDOWN

pytestmark = pytest.mark.django_db


def _write_markdown(tmp_path, body='# Estimate\n\nDemo content.\n'):
    md_file = tmp_path / 'estimate.md'
    md_file.write_text(body, encoding='utf-8')
    return md_file


def _run(md_file, title='Estimate: demo — 01072026', **extra):
    args = ['--title', title, '--file', str(md_file)]
    for flag, value in extra.items():
        args += [f'--{flag}', value]
    call_command('create_estimate_document', *args)


class TestCreateEstimateDocument:
    def test_creates_document_in_default_folder(self, tmp_path):
        _run(_write_markdown(tmp_path))

        document = Document.objects.get(title='Estimate: demo — 01072026')
        assert document.folder.name == 'Requirement Estimates'
        assert document.folder.parent is None
        assert document.document_type.code == MARKDOWN

    def test_folder_is_created_only_once_across_runs(self, tmp_path):
        md_file = _write_markdown(tmp_path)
        _run(md_file, title='Estimate: uno — 01072026')
        _run(md_file, title='Estimate: dos — 01072026')

        assert DocumentFolder.objects.filter(name='Requirement Estimates').count() == 1
        assert Document.objects.filter(folder__name='Requirement Estimates').count() == 2

    def test_content_status_and_language_are_persisted(self, tmp_path):
        md_file = _write_markdown(tmp_path, body='# Custom body\n')
        _run(md_file, status='draft', language='en')

        document = Document.objects.get()
        assert document.content_markdown == '# Custom body\n'
        assert document.status == Document.Status.DRAFT
        assert document.language == Document.Language.EN

    def test_custom_folder_name_is_used(self, tmp_path):
        _run(_write_markdown(tmp_path), folder='Other Estimates')

        assert Document.objects.get().folder.name == 'Other Estimates'

    def test_missing_file_raises_command_error(self, tmp_path):
        with pytest.raises(CommandError, match='not found'):
            _run(tmp_path / 'does-not-exist.md')
        assert not Document.objects.exists()

    def test_empty_file_raises_command_error(self, tmp_path):
        with pytest.raises(CommandError, match='empty'):
            _run(_write_markdown(tmp_path, body='   \n'))
        assert not Document.objects.exists()

    def test_same_title_creates_versioned_document(self, tmp_path):
        md_file = _write_markdown(tmp_path)
        _run(md_file)
        _run(md_file)

        titles = set(Document.objects.values_list('title', flat=True))
        assert titles == {
            'Estimate: demo — 01072026',
            'Estimate: demo — 01072026 — v2',
        }

    def test_on_conflict_replace_updates_newest_without_creating(self, tmp_path):
        _run(_write_markdown(tmp_path, body='# Original\n'))
        md_file = _write_markdown(tmp_path, body='# Corrected\n')
        call_command(
            'create_estimate_document',
            '--title', 'Estimate: demo — 01072026',
            '--file', str(md_file),
            '--on-conflict', 'replace',
        )

        document = Document.objects.get()
        assert document.content_markdown == '# Corrected\n'

    def test_output_includes_panel_url(self, tmp_path):
        out = StringIO()
        call_command(
            'create_estimate_document',
            '--title', 'Estimate: demo — 01072026',
            '--file', str(_write_markdown(tmp_path)),
            stdout=out,
        )

        document = Document.objects.get()
        assert f'Panel URL: /panel/documents/{document.pk}/edit' in out.getvalue()
