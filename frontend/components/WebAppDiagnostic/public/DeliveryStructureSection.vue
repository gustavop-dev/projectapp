<template>
  <section>
    <SectionHeader :index="content.index" :title="content.title" fallback="Estructura de la Entrega" />
    <p v-if="content.intro" class="text-gray-700 mb-6">{{ content.intro }}</p>

    <div class="grid md:grid-cols-3 gap-4">
      <div
        v-for="(b, idx) in content.blocks"
        :key="idx"
        class="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm"
      >
        <h3 class="font-semibold text-gray-900 mb-2">{{ b.title }}</h3>
        <p v-for="(p, i) in b.paragraphs" :key="i" class="text-sm text-gray-600 leading-relaxed">{{ p }}</p>
        <blockquote v-if="b.example" class="mt-3 border-l-2 border-emerald-400 pl-3 text-xs italic text-emerald-700">
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
