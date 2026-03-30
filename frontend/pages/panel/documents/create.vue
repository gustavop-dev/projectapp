<template>
  <div>
    <div class="mb-8">
      <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 transition-colors">
        ← Volver a documentos
      </NuxtLink>
      <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100 mt-2">Nuevo Documento</h1>
    </div>

    <!-- Tab toggle -->
    <div class="flex gap-1 mb-6 bg-gray-100 dark:bg-gray-700 rounded-xl p-1 max-w-md">
      <button
        type="button"
        :class="[
          'flex-1 px-4 py-2 text-sm rounded-lg transition-all',
          mode === 'paste' ? 'bg-white dark:bg-gray-800 shadow-sm font-medium text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
        ]"
        @click="mode = 'paste'"
      >
        Pegar Markdown
      </button>
      <button
        type="button"
        :class="[
          'flex-1 px-4 py-2 text-sm rounded-lg transition-all',
          mode === 'upload' ? 'bg-white dark:bg-gray-800 shadow-sm font-medium text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
        ]"
        @click="mode = 'upload'"
      >
        Cargar Archivo
      </button>
    </div>

    <!-- Shared metadata fields -->
    <form class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-8 dark:bg-gray-800 dark:border-gray-700" :class="showPreview && mode === 'paste' ? 'max-w-6xl' : 'max-w-2xl'" @submit.prevent="handleSubmit">
      <div class="space-y-6">
        <!-- Title -->
        <div>
          <label for="doc-title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Titulo *</label>
          <input
            id="doc-title"
            v-model="form.title"
            type="text"
            required
            placeholder="Mi Documento"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                   dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
          />
        </div>

        <!-- Client name -->
        <div>
          <label for="doc-client" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nombre del cliente</label>
          <input
            id="doc-client"
            v-model="form.client_name"
            type="text"
            placeholder="Empresa S.A."
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
                   dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
          />
        </div>

        <!-- Language + Cover toggle -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Idioma</label>
            <select
              v-model="form.language"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white
                     dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200"
            >
              <option value="es">Espanol</option>
              <option value="en">English</option>
            </select>
          </div>
          <div class="flex flex-col justify-end">
            <label class="flex items-center gap-3 cursor-pointer py-2.5 px-1 group select-none">
              <span class="relative flex-shrink-0">
                <input
                  v-model="withCovers"
                  type="checkbox"
                  class="sr-only peer"
                />
                <span
                  class="block w-10 h-6 rounded-full transition-colors duration-200
                         bg-gray-200 peer-checked:bg-emerald-500
                         dark:bg-gray-600 dark:peer-checked:bg-emerald-500"
                ></span>
                <span
                  class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200
                         peer-checked:translate-x-4"
                ></span>
              </span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Incluir portada y contraportada
              </span>
            </label>
          </div>
        </div>

        <!-- Tab 1: Paste Markdown -->
        <div v-if="mode === 'paste'">
          <div class="flex items-center justify-between mb-1">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Contenido Markdown</label>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors"
              :class="showPreview
                ? 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400 dark:hover:bg-emerald-900/50'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-400 dark:hover:bg-gray-600'"
              @click="showPreview = !showPreview"
            >
              <svg v-if="showPreview" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
              </svg>
              {{ showPreview ? 'Ocultar vista previa' : 'Vista previa' }}
            </button>
          </div>
          <div :class="showPreview ? 'grid grid-cols-1 lg:grid-cols-2 gap-4' : ''">
            <!-- Textarea editor -->
            <textarea
              v-model="form.content_markdown"
              rows="16"
              placeholder="# Mi Documento&#10;&#10;Escribe o pega tu contenido en formato Markdown..."
              class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm font-mono leading-relaxed
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-y
                     dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
            ></textarea>
            <!-- Preview panel -->
            <div
              v-if="showPreview"
              class="border border-gray-200 rounded-xl bg-white overflow-y-auto dark:bg-gray-900 dark:border-gray-600"
              style="min-height: 24rem; max-height: 40rem;"
            >
              <div class="px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 rounded-t-xl">
                <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Vista previa</span>
              </div>
              <div
                v-if="form.content_markdown.trim()"
                class="markdown-preview px-5 py-4"
                v-html="previewHtml"
              ></div>
              <div
                v-else
                class="flex items-center justify-center h-64 text-sm text-gray-400 dark:text-gray-500"
              >
                Escribe markdown para ver la vista previa...
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 2: Upload File -->
        <div v-if="mode === 'upload'">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Archivo Markdown (.md)</label>
          <div class="flex items-center gap-3 mb-3">
            <label
              class="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     text-gray-700 hover:bg-gray-50 cursor-pointer transition-colors
                     dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Seleccionar archivo
              <input type="file" accept=".md,.markdown,.txt" class="hidden" @change="handleFileUpload" />
            </label>
            <span v-if="uploadedFileName" class="text-xs text-gray-500 dark:text-gray-400">{{ uploadedFileName }}</span>
          </div>
          <textarea
            v-model="form.content_markdown"
            rows="16"
            readonly
            placeholder="El contenido del archivo aparecera aqui..."
            class="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm font-mono leading-relaxed
                   bg-gray-50 outline-none resize-y
                   dark:bg-gray-700/50 dark:border-gray-600 dark:text-gray-300 dark:placeholder-gray-500"
          ></textarea>
        </div>

        <!-- Errors -->
        <div v-if="errorMsg" class="text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl dark:bg-red-900/20 dark:text-red-400">
          {{ errorMsg }}
        </div>

        <!-- Submit -->
        <div class="flex flex-wrap items-center gap-4 pt-2">
          <button
            type="submit"
            :disabled="documentStore.isUpdating || !form.title.trim() || !form.content_markdown.trim()"
            class="px-5 sm:px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                   hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
          >
            {{ documentStore.isUpdating ? 'Creando...' : 'Crear Documento' }}
          </button>
          <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
            Cancelar
          </NuxtLink>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const errorMsg = ref('');
const mode = ref('paste');
const uploadedFileName = ref('');
const showPreview = ref(true);

const form = reactive({
  title: '',
  client_name: '',
  language: 'es',
  cover_type: 'generic',
  content_markdown: '',
});

/** Toggle: true = cover_type 'generic', false = cover_type 'none'. */
const withCovers = computed({
  get: () => form.cover_type !== 'none',
  set: (val) => { form.cover_type = val ? 'generic' : 'none'; },
});

/** Lightweight markdown-to-HTML renderer (no external dependencies). */
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
  // Matches consecutive `> ` lines; if first line is [!TYPE], renders as callout div.
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

  // --- Headings (must come before list processing) ---
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>');

  // --- Horizontal rules ---
  html = html.replace(/^---+$/gm, '<hr class="md-hr" />');

  // --- Nested + flat list builder ---
  // Builds HTML for a block of consecutive list lines (may include indented sub-items).
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

const previewHtml = computed(() => parseMarkdown(form.content_markdown));

function handleFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  uploadedFileName.value = file.name;
  const reader = new FileReader();
  reader.onload = (e) => {
    form.content_markdown = e.target?.result || '';
  };
  reader.readAsText(file);
}

function formatError(errors) {
  if (errors && typeof errors === 'object') {
    return Object.entries(errors)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join(' | ');
  }
  return 'Error al crear el documento.';
}

async function handleSubmit() {
  errorMsg.value = '';
  const payload = {
    title: form.title.trim(),
    client_name: form.client_name.trim(),
    language: form.language,
    cover_type: form.cover_type,
    markdown: form.content_markdown,
  };

  const result = await documentStore.createFromMarkdown(payload);
  if (result.success) {
    navigateTo(localePath(`/panel/documents/${result.data.id}/edit`));
  } else {
    errorMsg.value = formatError(result.errors);
  }
}
</script>

<style scoped>
/* Markdown preview typography styles */
.markdown-preview :deep(.md-h1) {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.3;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #d1d5db;
  color: #047857;
}
.markdown-preview :deep(.md-h2) {
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.35;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  color: #047857;
}
.markdown-preview :deep(.md-h3) {
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.4;
  margin-top: 1rem;
  margin-bottom: 0.4rem;
  color: #059669;
}
.markdown-preview :deep(.md-p) {
  margin-bottom: 0.75rem;
  line-height: 1.7;
  font-size: 0.875rem;
  color: #374151;
}
.markdown-preview :deep(.md-ul),
.markdown-preview :deep(.md-ol) {
  margin-bottom: 0.75rem;
  padding-left: 1.5rem;
  font-size: 0.875rem;
  color: #374151;
}
.markdown-preview :deep(.md-ul) {
  list-style-type: disc;
}
.markdown-preview :deep(.md-ol) {
  list-style-type: decimal;
}
.markdown-preview :deep(.md-ul li),
.markdown-preview :deep(.md-ol li) {
  margin-bottom: 0.25rem;
  line-height: 1.6;
}
.markdown-preview :deep(.md-blockquote) {
  border-left: 3px solid #10b981;
  background-color: #f0fdf4;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  font-style: italic;
  font-size: 0.875rem;
  color: #4b5563;
  border-radius: 0 0.5rem 0.5rem 0;
}
.markdown-preview :deep(.md-code-block) {
  background-color: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  overflow-x: auto;
  font-size: 0.8rem;
  line-height: 1.6;
}
.markdown-preview :deep(.md-code-block code) {
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  color: #1f2937;
}
.markdown-preview :deep(.md-inline-code) {
  background-color: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 0.25rem;
  padding: 0.125rem 0.375rem;
  font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 0.825em;
  color: #dc2626;
}
.markdown-preview :deep(.md-table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 0.75rem;
  font-size: 0.8rem;
}
.markdown-preview :deep(.md-table th) {
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
}
.markdown-preview :deep(.md-table td) {
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  color: #4b5563;
}
.markdown-preview :deep(.md-table tbody tr:nth-child(even)) {
  background-color: #f9fafb;
}
.markdown-preview :deep(.md-hr) {
  border: none;
  border-top: 1px solid #d1d5db;
  margin: 1.25rem 0;
}
.markdown-preview :deep(.md-link) {
  color: #059669;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.markdown-preview :deep(.md-link:hover) {
  color: #047857;
}
.markdown-preview :deep(strong) {
  font-weight: 600;
}
.markdown-preview :deep(em) {
  font-style: italic;
}

/* Dark mode overrides — use :global(.dark) to reach <html class="dark"> from scoped context */
:global(.dark) .markdown-preview :deep(.md-h1) {
  color: #6ee7b7;
  border-bottom-color: #374151;
}
:global(.dark) .markdown-preview :deep(.md-h2) {
  color: #6ee7b7;
}
:global(.dark) .markdown-preview :deep(.md-h3) {
  color: #a7f3d0;
}
:global(.dark) .markdown-preview :deep(.md-p),
:global(.dark) .markdown-preview :deep(.md-ul),
:global(.dark) .markdown-preview :deep(.md-ol) {
  color: #d1d5db;
}
:global(.dark) .markdown-preview :deep(.md-ul li),
:global(.dark) .markdown-preview :deep(.md-ol li) {
  color: #d1d5db;
}
:global(.dark) .markdown-preview :deep(.md-blockquote) {
  background-color: rgba(16, 185, 129, 0.1);
  border-left-color: #10b981;
  color: #9ca3af;
}
:global(.dark) .markdown-preview :deep(.md-code-block) {
  background-color: #1f2937;
  border-color: #374151;
}
:global(.dark) .markdown-preview :deep(.md-code-block code) {
  color: #e5e7eb;
}
:global(.dark) .markdown-preview :deep(.md-inline-code) {
  background-color: #1f2937;
  border-color: #374151;
  color: #f87171;
}
:global(.dark) .markdown-preview :deep(.md-table th) {
  background-color: #1f2937;
  border-color: #374151;
  color: #d1d5db;
}
:global(.dark) .markdown-preview :deep(.md-table td) {
  border-color: #374151;
  color: #9ca3af;
}
:global(.dark) .markdown-preview :deep(.md-table tbody tr:nth-child(even)) {
  background-color: rgba(31, 41, 55, 0.5);
}
:global(.dark) .markdown-preview :deep(.md-hr) {
  border-top-color: #374151;
}
:global(.dark) .markdown-preview :deep(.md-link) {
  color: #6ee7b7;
}
:global(.dark) .markdown-preview :deep(.md-link:hover) {
  color: #a7f3d0;
}

/* Strikethrough */
.markdown-preview :deep(del) {
  text-decoration: line-through;
  color: #6b7280;
}

/* Inline code */
.markdown-preview :deep(code) {
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.85em;
  background-color: #f3f4f6;
  color: #374151;
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid #e5e7eb;
}

/* Nested lists */
.markdown-preview :deep(ul ul),
.markdown-preview :deep(ol ol),
.markdown-preview :deep(ul ol),
.markdown-preview :deep(ol ul) {
  margin-top: 4px;
  margin-bottom: 4px;
  margin-left: 20px;
}

/* Callouts */
.markdown-preview :deep(.callout) {
  border-radius: 6px;
  padding: 10px 14px;
  margin: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.markdown-preview :deep(.callout-label) {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
}
.markdown-preview :deep(.callout-body) {
  font-size: 13px;
  line-height: 1.5;
}
.markdown-preview :deep(.callout-note) {
  background-color: #e6efef;
  border-left: 3px solid #002921;
}
.markdown-preview :deep(.callout-note .callout-label) { color: #002921; }
.markdown-preview :deep(.callout-tip) {
  background-color: #f0fff4;
  border-left: 3px solid #809490;
}
.markdown-preview :deep(.callout-tip .callout-label) { color: #809490; }
.markdown-preview :deep(.callout-important) {
  background-color: #eef2ff;
  border-left: 3px solid #6366f1;
}
.markdown-preview :deep(.callout-important .callout-label) { color: #6366f1; }
.markdown-preview :deep(.callout-warning) {
  background-color: #fffbeb;
  border-left: 3px solid #d97706;
}
.markdown-preview :deep(.callout-warning .callout-label) { color: #d97706; }
.markdown-preview :deep(.callout-caution) {
  background-color: #fff1f2;
  border-left: 3px solid #f43f5e;
}
.markdown-preview :deep(.callout-caution .callout-label) { color: #f43f5e; }

/* Dark mode overrides for new elements */
:global(.dark) .markdown-preview :deep(del) { color: #9ca3af; }
:global(.dark) .markdown-preview :deep(code) {
  background-color: #374151;
  color: #d1d5db;
  border-color: #4b5563;
}
:global(.dark) .markdown-preview :deep(.callout-note) {
  background-color: #0d2b24;
  border-color: #809490;
}
:global(.dark) .markdown-preview :deep(.callout-tip) {
  background-color: #052e16;
  border-color: #4ade80;
}
:global(.dark) .markdown-preview :deep(.callout-tip .callout-label) { color: #4ade80; }
:global(.dark) .markdown-preview :deep(.callout-important) {
  background-color: #1e1b4b;
  border-color: #818cf8;
}
:global(.dark) .markdown-preview :deep(.callout-important .callout-label) { color: #818cf8; }
:global(.dark) .markdown-preview :deep(.callout-warning) {
  background-color: #1c1400;
  border-color: #fbbf24;
}
:global(.dark) .markdown-preview :deep(.callout-warning .callout-label) { color: #fbbf24; }
:global(.dark) .markdown-preview :deep(.callout-caution) {
  background-color: #200a0e;
  border-color: #fb7185;
}
:global(.dark) .markdown-preview :deep(.callout-caution .callout-label) { color: #fb7185; }
</style>
