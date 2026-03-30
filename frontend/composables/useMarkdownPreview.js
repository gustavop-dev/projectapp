export function useMarkdownPreview() {
  const parseMarkdown = (md) => {
    if (!md) return '';

    let html = md;

    // Normalize line endings
    html = html.replace(/\r\n/g, '\n');

    // --- Fenced code blocks (``` ... ```) ---
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, _lang, code) => {
      const escaped = code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
      return `<pre class="md-code-block"><code>${escaped.trimEnd()}</code></pre>`;
    });

    // --- Tables ---
    html = html.replace(
      /((?:^\|.+\|[ \t]*\n)+)/gm,
      (tableBlock) => {
        const rows = tableBlock.trim().split('\n');
        if (rows.length < 2) return tableBlock;

        // Check if second row is a separator row (e.g. |---|---|)
        const separatorMatch = rows[1].match(/^\|[\s:]*-{2,}[\s:]*(\|[\s:]*-{2,}[\s:]*)*\|$/);
        const hasSeparator = !!separatorMatch;
        const dataRows = hasSeparator ? [rows[0], ...rows.slice(2)] : rows;

        let table = '<table class="md-table">';

        dataRows.forEach((row, idx) => {
          const cells = row.split('|').slice(1, -1); // remove leading/trailing empty
          if (idx === 0 && hasSeparator) {
            table += '<thead><tr>';
            cells.forEach((cell) => {
              table += `<th>${cell.trim()}</th>`;
            });
            table += '</tr></thead><tbody>';
          } else {
            table += '<tr>';
            cells.forEach((cell) => {
              table += `<td>${cell.trim()}</td>`;
            });
            table += '</tr>';
          }
        });

        if (hasSeparator) table += '</tbody>';
        table += '</table>';
        return table;
      },
    );

    // --- Inline formatting helper ---
    // Applied to text nodes; order matters — most specific patterns first.
    const applyInline = (text) => {
      // 1. Bold-italic
      text = text.replace(/\*{3}(.+?)\*{3}/g, '<strong><em>$1</em></strong>');
      // 2. Bold (after bold-italic so *** is already consumed)
      text = text.replace(/\*{2}(.+?)\*{2}/g, '<strong>$1</strong>');
      // 3. Italic (single star, not preceded/followed by another star)
      text = text.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
      // 4. Strikethrough
      text = text.replace(/~~(.+?)~~/g, '<del>$1</del>');
      // 5. Inline code
      text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
      // 6. Markdown links
      text = text.replace(
        /\[([^\]]+)\]\(([^)]+)\)/g,
        '<a href="$2" class="md-link" target="_blank" rel="noopener noreferrer">$1</a>',
      );
      return text;
    };

    // --- Callout blocks (GitHub-style, must come BEFORE blockquote processing) ---
    html = html.replace(
      /(^>\s?.+(?:\n>\s?.+)*)/gm,
      (match) => {
        const lines = match.split('\n');
        const firstContent = lines[0].replace(/^>\s?/, '');
        const calloutMatch = firstContent.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]$/i);
        if (calloutMatch) {
          const type = calloutMatch[1].toLowerCase();
          const labelMap = {
            note: 'NOTA',
            tip: 'CONSEJO',
            important: 'IMPORTANTE',
            warning: 'AVISO',
            caution: 'PRECAUCIÓN',
          };
          const label = labelMap[type];
          const bodyLines = lines.slice(1).map((l) => l.replace(/^>\s?/, ''));
          const body = applyInline(bodyLines.join(' ').trim());
          return `<div class="callout callout-${type}"><span class="callout-label">${label}</span><span class="callout-body">${body}</span></div>`;
        }
        // Fall through to regular blockquote
        const content = match.replace(/^>\s?/gm, '');
        return `<blockquote class="md-blockquote">${content}</blockquote>`;
      },
    );

    // --- Headings H1–H6 (most specific first) ---
    html = html.replace(/^###### (.+)$/gm, '<h6 class="md-h6">$1</h6>');
    html = html.replace(/^##### (.+)$/gm, '<h5 class="md-h5">$1</h5>');
    html = html.replace(/^#### (.+)$/gm, '<h4 class="md-h4">$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>');

    // --- Horizontal rules ---
    html = html.replace(/^---+$/gm, '<hr class="md-hr" />');

    // --- Nested + flat list builder ---
    const buildListHtml = (listLines, ordered) => {
      const result = [];
      let currentItem = null;
      for (const line of listLines) {
        const isNested = /^(\s{2,}|\t)/.test(line);
        if (isNested) {
          const text = line.replace(/^(\s{2,}|\t)[-*+\d.]+\s+/, '').trim();
          if (currentItem) currentItem.children.push(text);
        } else {
          const text = line.replace(/^[-*+\d.]+\s+/, '').trim();
          currentItem = { text, children: [] };
          result.push(currentItem);
        }
      }
      const tag = ordered ? 'ol' : 'ul';
      const cls = ordered ? 'md-ol' : 'md-ul';
      return `<${tag} class="${cls}">${result.map((item) => {
        const childHtml = item.children.length
          ? `<${tag} class="${cls}">${item.children.map((c) => `<li>${applyInline(c)}</li>`).join('')}</${tag}>`
          : '';
        return `<li>${applyInline(item.text)}${childHtml}</li>`;
      }).join('')}</${tag}>`;
    };

    // --- Unordered lists (nested-aware) ---
    html = html.replace(
      /(^[ \t]*[-*+] .+(?:\n[ \t]*[-*+] .+)*)/gm,
      (match) => buildListHtml(match.split('\n'), false),
    );

    // --- Ordered lists (nested-aware) ---
    html = html.replace(
      /(^[ \t]*\d+\. .+(?:\n[ \t]*\d+\. .+)*)/gm,
      (match) => buildListHtml(match.split('\n'), true),
    );

    // Apply inline formatting across the whole document
    // (split on HTML tags so we only touch text nodes, not existing markup)
    html = html
      .split(/(<[^>]+>)/)
      .map((chunk) => (chunk.startsWith('<') ? chunk : applyInline(chunk)))
      .join('');

    // --- Paragraphs: wrap remaining loose lines ---
    html = html
      .split('\n\n')
      .map((block) => {
        const trimmed = block.trim();
        if (!trimmed) return '';
        // Don't wrap blocks that are already HTML block-level elements
        if (/^<(h[1-6]|ul|ol|li|pre|table|thead|tbody|tr|th|td|blockquote|hr|div)[\s>]/i.test(trimmed)) {
          return trimmed;
        }
        return `<p class="md-p">${trimmed.replace(/\n/g, '<br />')}</p>`;
      })
      .join('\n');

    return html;
  };

  return { parseMarkdown };
}
