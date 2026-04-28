<template>
  <section ref="sectionRef" class="raw-content min-h-screen w-full bg-surface py-16" data-testid="raw-content">
    <div class="w-full px-6 md:px-12 lg:px-24">
      <div class="max-w-4xl mx-auto">
        <div data-animate="fade-up" class="flex items-baseline gap-4 mb-10">
          <span v-if="index" data-testid="raw-content-index" class="text-text-muted font-light tracking-[0.25em] text-xs md:text-sm">
            {{ index }}
          </span>
          <h2 class="text-text-brand font-light leading-tight text-4xl md:text-6xl">
            {{ title }}
          </h2>
        </div>

        <div
          data-animate="fade-up"
          class="raw-content-card bg-gray-50/80 backdrop-blur-sm border border-border-default/60
                 rounded-2xl p-5 sm:p-8 md:p-12 shadow-sm prose prose-emerald max-w-none"
          data-testid="raw-content-card"
          v-html="renderedHtml"
        />
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { useSectionAnimations } from '~/composables/useSectionAnimations';

const sectionRef = ref(null);
useSectionAnimations(sectionRef);

const props = defineProps({
  title: { type: String, default: '' },
  index: { type: String, default: '' },
  rawText: { type: String, default: '' },
});

const renderedHtml = computed(() => {
  if (!props.rawText) return '';
  const html = marked.parse(props.rawText, { breaks: true });
  return DOMPurify.sanitize(html);
});
</script>

<style scoped>
.prose h1, .prose h2, .prose h3, .prose h4 {
  color: #064e3b;
}
.prose p {
  color: #374151;
  line-height: 1.75;
}
.prose ul, .prose ol {
  color: #374151;
}
.prose strong {
  color: #064e3b;
}
.raw-content-card {
  font-size: 1rem;
}
</style>
