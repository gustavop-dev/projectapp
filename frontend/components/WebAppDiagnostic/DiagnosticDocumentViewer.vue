<template>
  <article
    class="prose prose-emerald max-w-none diagnostic-doc"
    v-html="renderedHtml"
  />
</template>

<script setup>
import { computed } from 'vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const props = defineProps({
  markdown: { type: String, default: '' },
});

const renderedHtml = computed(() => {
  if (!props.markdown) return '';
  const html = marked.parse(props.markdown, { breaks: true, gfm: true });
  return DOMPurify.sanitize(html);
});
</script>

<style scoped>
.diagnostic-doc :deep(h1),
.diagnostic-doc :deep(h2),
.diagnostic-doc :deep(h3),
.diagnostic-doc :deep(h4) {
  color: #064e3b;
}
.diagnostic-doc :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 0.92em;
}
.diagnostic-doc :deep(th),
.diagnostic-doc :deep(td) {
  border: 1px solid #d1d5db;
  padding: 0.5rem 0.75rem;
  text-align: left;
  vertical-align: top;
}
.diagnostic-doc :deep(th) {
  background-color: #f0fdfa;
  font-weight: 600;
}
.diagnostic-doc :deep(blockquote) {
  border-left: 4px solid #0f766e;
  background: #f0fdfa;
  padding: 0.75rem 1rem;
  color: #134e4a;
  margin: 1em 0;
}
.diagnostic-doc :deep(code) {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}
</style>
