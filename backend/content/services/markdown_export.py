"""Small, bounded Markdown primitives for document exports."""
from html import escape, unescape
import re

from django.utils.html import strip_tags

MAX_MARKDOWN_CHARACTERS = 1_000_000


class MarkdownExportError(ValueError):
    def __init__(self, message, code='invalid_document', status=422):
        super().__init__(message)
        self.code = code
        self.status = status


def literal(value):
    """Escape document text without interpreting it as HTML or Markdown."""
    value = '' if value is None else str(value)
    value = re.sub(r'([\\`*_{}\[\]|~])', r'\\\1', value)
    value = re.sub(r'(?m)^(\s*)([#>+-]|\d+[.)])', r'\1\\\2', value)
    return escape(value, quote=False)


def formal_text(value):
    return literal(unescape(strip_tags(str(value or ''))))


def table(headers, rows):
    def line(cells):
        return '| ' + ' | '.join(str(cell).replace('\n', '<br>') for cell in cells) + ' |'

    return '\n'.join([line(headers), line(['---'] * len(headers)), *(line(row) for row in rows)])


class MarkdownBuffer:
    """Reject oversized exports before accumulating unbounded output."""

    def __init__(self):
        self.parts = []
        self.length = 0

    def append(self, value):
        if not value.strip():
            return
        self.length += len(value) + 2
        if self.length > MAX_MARKDOWN_CHARACTERS:
            raise MarkdownExportError('El documento supera el límite de un millón de caracteres.', 'document_too_large', 413)
        self.parts.append(value)

    def render(self):
        result = '\n\n'.join(self.parts).strip()
        if not result:
            raise MarkdownExportError('El archivo no contiene texto extraíble. Las imágenes y los escaneos requieren reconocimiento de texto.', 'text_unavailable')
        return result + '\n'


def export_payload(title, markdown, warnings=()):
    buffer = MarkdownBuffer()
    buffer.append(markdown)
    return {'title': title, 'markdown': buffer.render(), 'warnings': list(warnings)}
