<template>
  <div class="min-h-screen bg-surface-muted">
    <main class="w-full py-20 px-6 lg:px-32">
      <div class="max-w-4xl mx-auto">
        <h1 class="text-4xl lg:text-6xl font-bold text-text-brand mb-4">
          {{ messages?.title || 'Terms and Conditions' }}
        </h1>
        <p class="text-sm font-light text-green-light mb-8">
          {{ messages?.last_updated || '' }}
        </p>
        <p class="text-lg lg:text-xl font-light text-text-brand mb-12 leading-relaxed">
          {{ messages?.intro || '' }}
        </p>

        <!-- Definitions -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.definitions?.title }}
          </h2>
          <ul class="list-disc list-inside space-y-2">
            <li
              v-for="(item, idx) in sections?.definitions?.items || []"
              :key="idx"
              class="text-base lg:text-lg font-light text-text-brand leading-relaxed"
            >
              {{ item }}
            </li>
          </ul>
        </section>

        <!-- Services -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.services?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.services?.text }}
          </p>
        </section>

        <!-- Intellectual Property -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.intellectual_property?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-4">
            {{ sections?.intellectual_property?.text_1 }}
          </p>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.intellectual_property?.text_2 }}
          </p>
        </section>

        <!-- Payments -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.payments?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-4">
            {{ sections?.payments?.text_1 }}
          </p>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.payments?.text_2 }}
          </p>
        </section>

        <!-- Warranties -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.warranties?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-4">
            {{ sections?.warranties?.text_1 }}
          </p>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.warranties?.text_2 }}
          </p>
        </section>

        <!-- Termination -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.termination?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.termination?.text }}
          </p>
        </section>

        <!-- Confidentiality -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.confidentiality?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.confidentiality?.text }}
          </p>
        </section>

        <!-- Governing Law -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.governing_law?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.governing_law?.text }}
          </p>
        </section>

        <!-- Changes -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.changes?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.changes?.text }}
          </p>
        </section>

        <!-- Contact -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.contact?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-2">
            {{ sections?.contact?.text }}
          </p>
          <a
            :href="`mailto:${sections?.contact?.email || 'team@projectapp.co'}`"
            class="text-lg font-medium text-text-brand underline hover:text-text-brand transition-colors"
          >
            {{ sections?.contact?.email || 'team@projectapp.co' }}
          </a>
        </section>

        <!-- Back link -->
        <div class="mt-16 pt-8 border-t border-border-default">
          <NuxtLink
            :to="localePath('/')"
            class="inline-flex items-center text-lg font-medium text-text-brand hover:text-text-brand transition-colors"
          >
            <span class="mr-2">&larr;</span>
            {{ backLabel }}
          </NuxtLink>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useMessages } from '~/composables/useMessages'

const localePath = useLocalePath()
const { messages } = useMessages('termsAndConditions')

const sections = computed(() => messages.value?.sections || {})

const { locale } = useI18n()
const backLabel = computed(() =>
  locale.value === 'es-co' ? 'Volver al inicio' : 'Back to home'
)
</script>
