<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Estructura de la Entrega" />
    <p v-if="content.intro" class="text-text-brand/80 dark:text-text-brand/80 mb-6">{{ content.intro }}</p>

    <div class="grid md:grid-cols-3 gap-4">
      <div
        v-for="(b, idx) in content.blocks"
        :key="idx"
        class="bg-surface dark:bg-primary-soft/5 border border-input-border/10 dark:border-input-border/15 rounded-2xl p-5 shadow-sm hover:shadow-md hover:border-input-border/20 dark:hover:border-input-border/25 transition"
      >
        <h3 class="font-semibold text-text-brand dark:text-text-brand mb-2">{{ b.title }}</h3>
        <p v-for="(p, i) in b.paragraphs" :key="i" class="text-sm text-text-brand/75 dark:text-text-brand/75 leading-relaxed">{{ p }}</p>
        <blockquote v-if="b.example" class="mt-3 border-l-2 border-input-border/40 dark:border-input-border/40 pl-3 text-xs italic text-text-brand/80 dark:text-text-brand/80">
          Ejemplo: {{ b.example }}
        </blockquote>
      </div>
    </div>
  </section>
</template>

<script setup>
import SectionHeader from './SectionHeader.vue';
defineProps({ content: { type: Object, required: true } });
</script>
