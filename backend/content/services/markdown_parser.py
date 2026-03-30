"""
Markdown-to-blocks parser for the Document PDF system.

Converts Markdown text into a flat list of typed block dicts
that the DocumentPdfService can render into a branded PDF.
"""

import re

_CALLOUT_RE = re.compile(r'^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]$', re.IGNORECASE)


def markdown_to_blocks(text):
    """Convert Markdown text into a list of block dicts.

    Supported block types:
    - heading: # H1, ## H2, ### H3
    - paragraph: regular text (consecutive non-empty lines merged)
    - table: lines starting with |
    - list (unordered): lines starting with - or *
    - list (ordered): lines starting with 1. 2. etc.
    - blockquote: lines starting with >
    - code: fenced with ```
    - separator: --- or *** or ___
    - section_header: ### with numbered pattern like "### 1. Title"
    - sub_section: **N.N. Title** pattern (bold numbered sub-heading)

    Returns:
        list[dict]: List of block objects.
    """
    blocks = []
    lines = text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # 1. Code blocks (highest priority)
        if stripped.startswith('```'):
            language = stripped[3:].strip() or 'text'
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1  # skip closing ```
            blocks.append({
                'type': 'code',
                'language': language,
                'content': '\n'.join(code_lines),
            })
            continue

        # 2. Separator
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            blocks.append({'type': 'separator'})
            i += 1
            continue

        # 3. Headings
        heading_match = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            title_text = heading_match.group(2).strip()
            # Check for numbered section: ### 1. Title or ### 14. Title
            section_match = re.match(r'^(\d+)\.\s+(.+)$', title_text)
            if level == 3 and section_match:
                index = section_match.group(1).zfill(2)
                blocks.append({
                    'type': 'section_header',
                    'index': index,
                    'title': section_match.group(2),
                })
            else:
                blocks.append({
                    'type': 'heading',
                    'level': level,
                    'text': title_text,
                })
            i += 1
            continue

        # 4. Blockquote / Callout
        if stripped.startswith('>'):
            quote_lines = []
            while i < len(lines):
                s = lines[i].strip()
                if s.startswith('> '):
                    quote_lines.append(s[2:])
                elif s == '>':
                    quote_lines.append('')
                else:
                    break
                i += 1
            if quote_lines:
                callout_match = _CALLOUT_RE.match(quote_lines[0].strip())
                if callout_match:
                    style = callout_match.group(1).lower()
                    body = ' '.join(ln for ln in quote_lines[1:] if ln).strip()
                    blocks.append({
                        'type': 'callout',
                        'style': style,
                        'text': body,
                    })
                else:
                    blocks.append({
                        'type': 'blockquote',
                        'text': ' '.join(ln for ln in quote_lines if ln).strip(),
                    })
            continue

        # 5. Table
        if stripped.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2:
                def parse_row(row_str):
                    cells = row_str.split('|')
                    if cells and not cells[0].strip():
                        cells = cells[1:]
                    if cells and not cells[-1].strip():
                        cells = cells[:-1]
                    return [c.strip() for c in cells]

                headers = parse_row(table_lines[0])
                rows = []
                for row_line in table_lines[1:]:
                    if re.match(r'^[\s|:\-]+$', row_line):
                        continue
                    rows.append(parse_row(row_line))
                blocks.append({
                    'type': 'table',
                    'headers': headers,
                    'rows': rows,
                })
            continue

        # 6. Unordered list
        if re.match(r'^[-*]\s+', stripped):
            items = []
            while i < len(lines):
                raw_line = lines[i]
                s = raw_line.strip()

                # Check for nested item (indented list marker)
                nested_m = re.match(r'^(?:\s{2,}|\t)[-*]\s+(.+)$', raw_line)
                if nested_m:
                    if items:
                        items[-1]['children'].append(nested_m.group(1).strip())
                    i += 1
                    continue

                # Top-level unordered item
                m = re.match(r'^[-*]\s+(.+)$', s)
                if m:
                    items.append({'text': m.group(1), 'children': []})
                    i += 1
                    continue

                # Continuation line (non-empty, non-special) — append to last item text
                if (
                    s
                    and not s.startswith('#')
                    and not s.startswith('|')
                    and not s.startswith('>')
                    and not s.startswith('```')
                    and not re.match(r'^[-*_]{3,}\s*$', s)
                    and not re.match(r'^[-*]\s+', s)
                    and not re.match(r'^(?:\s{2,}|\t)[-*]\s+', raw_line)
                ):
                    if items:
                        items[-1]['text'] += ' ' + s
                    i += 1
                    continue

                break

            if items:
                blocks.append({
                    'type': 'list',
                    'ordered': False,
                    'items': items,
                })
            continue

        # 7. Ordered list
        if re.match(r'^\d+\.\s+', stripped):
            items = []
            while i < len(lines):
                raw_line = lines[i]
                s = raw_line.strip()

                # Check for nested item (indented ordered or unordered marker)
                nested_m = re.match(r'^(?:\s{2,}|\t)(?:[-*]|\d+\.)\s+(.+)$', raw_line)
                if nested_m:
                    if items:
                        items[-1]['children'].append(nested_m.group(1).strip())
                    i += 1
                    continue

                m = re.match(r'^\d+\.\s+(.+)$', s)
                if m:
                    items.append({'text': m.group(1), 'children': []})
                    i += 1
                    continue

                if (
                    s
                    and not s.startswith('#')
                    and not s.startswith('|')
                    and not re.match(r'^\d+\.', s)
                    and not re.match(r'^(?:\s{2,}|\t)(?:[-*]|\d+\.)\s+', raw_line)
                ):
                    if items:
                        items[-1]['text'] += ' ' + s
                    i += 1
                    continue

                break

            if items:
                blocks.append({
                    'type': 'list',
                    'ordered': True,
                    'items': items,
                })
            continue

        # 8. Sub-section: **N.N. Title** or **N.N Title**
        subsection_match = re.match(
            r'^\*\*(\d+\.\d+\.?)\s+(.+?)\*\*$', stripped,
        )
        if subsection_match:
            blocks.append({
                'type': 'sub_section',
                'index': subsection_match.group(1).rstrip('.'),
                'title': subsection_match.group(2),
            })
            i += 1
            continue

        # 9. Paragraph (fallback)
        para_lines = []
        while i < len(lines):
            s = lines[i].strip()
            if not s:
                break
            if (
                s.startswith('#')
                or s.startswith('|')
                or s.startswith('>')
                or s.startswith('```')
                or re.match(r'^[-*_]{3,}\s*$', s)
                or re.match(r'^[-*]\s+', s)
                or re.match(r'^\d+\.\s+', s)
                or re.match(r'^\*\*\d+\.\d+', s)
            ):
                break
            para_lines.append(s)
            i += 1
        if para_lines:
            blocks.append({
                'type': 'paragraph',
                'text': ' '.join(para_lines),
            })
        continue

    return blocks
