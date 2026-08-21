<template>
  <section class="min-h-screen bg-surface-raised px-4 py-12 sm:px-8 sm:py-16">
    <div class="relative mx-auto w-full max-w-4xl pb-3">
      <div
        aria-hidden="true"
        class="absolute inset-0 translate-x-2 translate-y-3 rounded-sm border border-border-muted bg-surface-muted shadow-card"
      />
      <div
        data-testid="contract-paper"
        role="document"
        :aria-label="terms?.title || copy.title"
        class="relative rounded-sm border border-border-default bg-surface shadow-raised"
      >
        <div class="p-5 sm:p-10 lg:p-14">
          <header class="mb-10 border-b border-border-default pb-8">
            <BaseBadge variant="warning" class="mb-4">{{ copy.draftLabel }}</BaseBadge>
            <h1 class="mb-3 text-3xl font-light text-text-brand sm:text-5xl">
              {{ terms?.title || copy.title }}
            </h1>
            <p class="text-sm leading-relaxed text-text-muted">{{ copy.notice }}</p>
          </header>

          <div v-if="loading" class="space-y-5" aria-live="polite">
            <p class="text-sm text-text-muted">{{ copy.loading }}</p>
            <div v-for="index in 8" :key="index" class="h-24 animate-pulse rounded-xl bg-surface-raised" />
          </div>

          <div v-else-if="error" class="rounded-2xl border border-danger-strong/30 bg-danger-soft p-6">
            <p class="mb-5 text-sm text-danger-strong">{{ copy.error }}</p>
            <BaseButton variant="secondary" @click="$emit('retry')">{{ copy.retry }}</BaseButton>
          </div>

          <div v-else data-testid="contract-terms-document">
            <div v-if="terms?.preamble_markdown" class="mb-10 rounded-2xl bg-surface-raised p-5 sm:p-8">
              <DocumentMarkdownBody
                :markdown="terms.preamble_markdown"
                variant="full"
                theme="professional"
              />
            </div>

            <article
              v-for="clause in clauses"
              :id="clause.id"
              :key="clause.id"
              class="scroll-mt-24 border-b border-border-default py-10 first:pt-0 last:border-0"
              :data-testid="`contract-clause-${clause.id}`"
            >
              <div class="mb-5 flex items-start gap-4">
                <span class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-warning-soft text-sm font-bold text-warning-strong">
                  {{ clause.number }}
                </span>
                <h2 class="pt-1 text-xl font-semibold leading-snug text-text-brand sm:text-2xl">
                  {{ clause.title }}
                </h2>
              </div>
              <DocumentMarkdownBody
                :markdown="clause.content_markdown"
                variant="full"
                theme="professional"
              />
            </article>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, watch } from 'vue';
import DocumentMarkdownBody from '~/components/panel/documents/DocumentMarkdownBody.vue';

const props = defineProps({
  terms: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  language: { type: String, default: 'es' },
});

const emit = defineEmits(['ready', 'retry']);

const translations = {
  es: {
    draftLabel: 'Borrador informativo · Sin firmas',
    title: 'Contrato de prestación de servicios',
    notice: 'Los datos personales aparecen enmascarados. La versión definitiva se formaliza por separado entre las partes.',
    loading: 'Preparando el documento…',
    error: 'El borrador no está disponible temporalmente.',
    retry: 'Reintentar',
  },
  en: {
    draftLabel: 'Informational draft · Unsigned',
    title: 'Service agreement',
    notice: 'Personal data is masked. The final version is executed separately by the parties.',
    loading: 'Preparing the document…',
    error: 'The draft is temporarily unavailable.',
    retry: 'Try again',
  },
};

const copy = computed(() => translations[props.language] || translations.es);
const clauses = computed(() => props.terms?.clauses || []);

watch(
  clauses,
  async currentClauses => {
    if (!currentClauses.length) return;
    await nextTick();
    emit('ready');
  },
  { immediate: true },
);
</script>
