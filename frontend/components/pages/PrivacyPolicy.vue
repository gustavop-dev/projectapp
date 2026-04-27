<template>
  <div class="min-h-screen bg-surface-muted">
    <main class="w-full py-20 px-6 lg:px-32">
      <div class="max-w-4xl mx-auto">
        <h1 class="text-4xl lg:text-6xl font-bold text-text-brand mb-4">
          {{ messages?.title || 'Privacy Policy' }}
        </h1>
        <p class="text-sm font-light text-green-light mb-8">
          {{ messages?.last_updated || '' }}
        </p>
        <p class="text-lg lg:text-xl font-light text-text-brand mb-12 leading-relaxed">
          {{ messages?.intro || '' }}
        </p>

        <!-- Information Collected -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.information_collected?.title }}
          </h2>

          <h3 class="text-xl lg:text-2xl font-medium text-text-brand mb-3">
            {{ sections?.information_collected?.subtitle_personal }}
          </h3>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-3">
            {{ sections?.information_collected?.text_personal }}
          </p>
          <ul class="list-disc list-inside space-y-1 mb-6">
            <li
              v-for="(item, idx) in sections?.information_collected?.items_personal || []"
              :key="`personal-${idx}`"
              class="text-base lg:text-lg font-light text-text-brand leading-relaxed"
            >
              {{ item }}
            </li>
          </ul>

          <h3 class="text-xl lg:text-2xl font-medium text-text-brand mb-3">
            {{ sections?.information_collected?.subtitle_automatic }}
          </h3>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-3">
            {{ sections?.information_collected?.text_automatic }}
          </p>
          <ul class="list-disc list-inside space-y-1">
            <li
              v-for="(item, idx) in sections?.information_collected?.items_automatic || []"
              :key="`auto-${idx}`"
              class="text-base lg:text-lg font-light text-text-brand leading-relaxed"
            >
              {{ item }}
            </li>
          </ul>
        </section>

        <!-- Use of Information -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.use_of_information?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-3">
            {{ sections?.use_of_information?.text }}
          </p>
          <ul class="list-disc list-inside space-y-1">
            <li
              v-for="(item, idx) in sections?.use_of_information?.items || []"
              :key="`use-${idx}`"
              class="text-base lg:text-lg font-light text-text-brand leading-relaxed"
            >
              {{ item }}
            </li>
          </ul>
        </section>

        <!-- Cookies -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.cookies?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-3">
            {{ sections?.cookies?.text }}
          </p>
          <ul class="list-disc list-inside space-y-1">
            <li
              v-for="(item, idx) in sections?.cookies?.items || []"
              :key="`cookie-${idx}`"
              class="text-base lg:text-lg font-light text-text-brand leading-relaxed"
            >
              {{ item }}
            </li>
          </ul>
        </section>

        <!-- Sharing -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.sharing?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-3">
            {{ sections?.sharing?.text }}
          </p>
          <ul class="list-disc list-inside space-y-1">
            <li
              v-for="(item, idx) in sections?.sharing?.items || []"
              :key="`share-${idx}`"
              class="text-base lg:text-lg font-light text-text-brand leading-relaxed"
            >
              {{ item }}
            </li>
          </ul>
        </section>

        <!-- Data Security -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.data_security?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.data_security?.text }}
          </p>
        </section>

        <!-- Data Retention -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.data_retention?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.data_retention?.text }}
          </p>
        </section>

        <!-- Your Rights -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.your_rights?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed mb-3">
            {{ sections?.your_rights?.text }}
          </p>
          <ul class="list-disc list-inside space-y-1">
            <li
              v-for="(item, idx) in sections?.your_rights?.items || []"
              :key="`rights-${idx}`"
              class="text-base lg:text-lg font-light text-text-brand leading-relaxed"
            >
              {{ item }}
            </li>
          </ul>
        </section>

        <!-- Third Party Links -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.third_party_links?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.third_party_links?.text }}
          </p>
        </section>

        <!-- Children -->
        <section class="mb-10">
          <h2 class="text-2xl lg:text-3xl font-bold text-text-brand mb-4">
            {{ sections?.children?.title }}
          </h2>
          <p class="text-base lg:text-lg font-light text-text-brand leading-relaxed">
            {{ sections?.children?.text }}
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
const { messages } = useMessages('privacyPolicy')

const sections = computed(() => messages.value?.sections || {})

const { locale } = useI18n()
const backLabel = computed(() =>
  locale.value === 'es-co' ? 'Volver al inicio' : 'Back to home'
)
</script>
