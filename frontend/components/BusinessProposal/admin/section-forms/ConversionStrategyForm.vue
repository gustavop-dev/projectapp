<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <FieldInput v-model="form.index" label="Índice" placeholder="3" />
    <FieldInput v-model="form.title" label="Título" />
  </div>
  <FieldTextarea v-model="form.intro" label="Introducción" :rows="4" :isSingle="true" />
  <!-- Steps: repeatable -->
  <div>
    <label class="block text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Pasos</label>
    <div v-for="(step, idx) in form.steps" :key="idx" class="mb-4 bg-surface-raised rounded-xl p-4 border border-border-muted">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs text-text-subtle">Paso {{ idx + 1 }}</span>
        <button type="button" class="text-xs text-danger-strong hover:text-danger-strong/80" @click="form.steps.splice(idx, 1)">Eliminar</button>
      </div>
      <FieldInput v-model="step.title" label="Título del paso" class="mb-2" />
      <FieldTextarea v-model="step.bullets" label="Bullets" help="Un bullet por línea" :rows="3" />
    </div>
    <button type="button" class="text-xs text-text-brand hover:text-text-brand font-medium" @click="form.steps.push({ title: '', bullets: '' })">
      + Agregar paso
    </button>
  </div>
  <FieldInput v-model="form.resultTitle" label="Título del resultado" />
  <FieldTextarea v-model="form.result" label="Resultado esperado" :rows="3" :isSingle="true" />
</template>

<script setup>
import { FieldInput, FieldTextarea } from './fields.js';

defineProps({
  form: { type: Object, required: true },
  proposalData: { type: Object, default: () => ({}) },
});
</script>
