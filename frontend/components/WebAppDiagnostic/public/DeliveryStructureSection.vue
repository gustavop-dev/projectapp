<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Estructura de la Entrega" />
    <p v-if="content.intro" class="text-esmerald/80 mb-6">{{ content.intro }}</p>

    <div class="grid md:grid-cols-3 gap-4">
      <div
        v-for="(b, idx) in content.blocks"
        :key="idx"
        class="bg-white border border-esmerald/10 rounded-2xl p-5 shadow-sm hover:shadow-md hover:border-esmerald/20 transition"
      >
        <h3 class="font-semibold text-esmerald mb-2">{{ b.title }}</h3>
        <p v-for="(p, i) in b.paragraphs" :key="i" class="text-sm text-esmerald/75 leading-relaxed">{{ p }}</p>
        <blockquote v-if="b.example" class="mt-3 border-l-2 border-esmerald/40 pl-3 text-xs italic text-esmerald/80">
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
