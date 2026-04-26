<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Estructura de la Entrega" />
    <p v-if="content.intro" class="text-esmerald/80 dark:text-esmerald-light/80 mb-6">{{ content.intro }}</p>

    <div class="grid md:grid-cols-3 gap-4">
      <div
        v-for="(b, idx) in content.blocks"
        :key="idx"
        class="bg-white dark:bg-esmerald-light/5 border border-esmerald/10 dark:border-esmerald-light/15 rounded-2xl p-5 shadow-sm hover:shadow-md hover:border-esmerald/20 dark:hover:border-esmerald-light/25 transition"
      >
        <h3 class="font-semibold text-esmerald dark:text-esmerald-light mb-2">{{ b.title }}</h3>
        <p v-for="(p, i) in b.paragraphs" :key="i" class="text-sm text-esmerald/75 dark:text-esmerald-light/75 leading-relaxed">{{ p }}</p>
        <blockquote v-if="b.example" class="mt-3 border-l-2 border-esmerald/40 dark:border-esmerald-light/40 pl-3 text-xs italic text-esmerald/80 dark:text-esmerald-light/80">
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
