"""Linux parser sandbox: bounded resources, JSON only, no Django setup."""
import json
import resource
import sys


def main():
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    from content.services.attachment_markdown import (
        MAX_FILE_BYTES, docx_markdown, pdf_markdown, xlsx_markdown,
    )
    from content.services.markdown_export import MarkdownExportError

    try:
        data = sys.stdin.buffer.read(MAX_FILE_BYTES + 1)
        if len(data) > MAX_FILE_BYTES:
            raise MarkdownExportError('El archivo supera el límite de 15 MB.', 'document_too_large', 413)
        markdown, warnings = {'.pdf': pdf_markdown, '.docx': docx_markdown, '.xlsx': xlsx_markdown}[sys.argv[1]](data)
        payload = {'markdown': markdown, 'warnings': warnings}
    except MarkdownExportError as exc:
        payload = {'error': str(exc), 'code': exc.code, 'status': exc.status}
    except MemoryError:
        payload = {'error': 'El archivo supera el límite de memoria para extracción.', 'code': 'extraction_limit', 'status': 413}
    except Exception:
        payload = {'error': 'No se pudo leer el archivo. Puede estar dañado o protegido.', 'code': 'invalid_document', 'status': 422}
    sys.stdout.write(json.dumps(payload, ensure_ascii=True))


if __name__ == '__main__':
    main()
