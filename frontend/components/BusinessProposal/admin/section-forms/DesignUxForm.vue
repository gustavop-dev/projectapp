<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <FieldInput v-model="form.index" label="Índice" placeholder="4" />
    <FieldInput v-model="form.title" label="Título" />
  </div>
  <FieldTextarea v-model="form.paragraphs" label="Párrafos" help="Un párrafo por línea" :rows="6" />
  <FieldInput v-model="form.focusTitle" label="Título de enfoque" />
  <FieldTextarea v-model="form.focusItems" label="Items de enfoque" help="Un item por línea" :rows="4" />
  <FieldInput v-model="form.objectiveTitle" label="Título del objetivo" />
  <FieldTextarea v-model="form.objective" label="Objetivo" :rows="3" :isSingle="true" />
</template>

<script setup>
import { FieldInput, FieldTextarea } from './fields.js';

defineProps({
  form: { type: Object, required: true },
  proposalData: { type: Object, default: () => ({}) },
});
</script>
