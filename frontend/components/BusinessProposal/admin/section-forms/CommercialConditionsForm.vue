<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <FieldInput v-model="form.index" label="Índice" placeholder="17" />
    <FieldInput v-model="form.title" label="Título" />
  </div>

  <!-- Paquetes de horas -->
  <div class="mt-2">
    <FieldInput v-model="form.packagesTitle" label="Título de los paquetes" />
    <FieldTextarea v-model="form.packagesIntro" label="Intro de los paquetes" :rows="2" :isSingle="true" class="mt-2" />

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
      <FieldInput
        :modelValue="form.hourlyRate"
        label="Tarifa base por hora"
        placeholder="90000"
        @update:modelValue="form.hourlyRate = $event"
      />
      <label class="block">
        <span class="block text-xs text-text-muted mb-0.5">Moneda</span>
        <select
          v-model="form.currency"
          class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text rounded-lg text-sm focus:ring-1 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
        >
          <option value="COP">COP</option>
          <option value="USD">USD</option>
        </select>
      </label>
    </div>

    <div class="mt-3 space-y-3">
      <div class="flex items-center justify-between">
        <label class="block text-xs font-medium text-text-muted uppercase tracking-wider">Paquetes</label>
        <button type="button" class="text-xs font-medium text-text-brand hover:underline" @click="addPackage">
          + Agregar paquete
        </button>
      </div>
      <div
        v-for="(pkg, idx) in form.packages"
        :key="idx"
        class="border border-border-default dark:border-white/[0.08] rounded-xl p-3 bg-surface-raised space-y-2"
      >
        <div class="flex items-center justify-between">
          <span class="text-[11px] text-text-muted uppercase tracking-wider">Paquete {{ idx + 1 }}</span>
          <button type="button" class="text-[11px] text-text-subtle hover:text-danger-strong" @click="removePackage(idx)">
            Quitar
          </button>
        </div>
        <FieldInput v-model="pkg.name" label="Nombre" placeholder="Paquete Ágil" />
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <FieldInput
            :modelValue="pkg.hours"
            label="Horas"
            placeholder="20"
            @update:modelValue="pkg.hours = $event"
          />
          <FieldInput
            :modelValue="pkg.discountPercent"
            label="Descuento %"
            placeholder="0"
            @update:modelValue="pkg.discountPercent = $event"
          />
          <FieldInput
            :modelValue="pkg.hourlyRate"
            label="Tarifa/h (opcional)"
            placeholder="Usa la tarifa base"
            @update:modelValue="pkg.hourlyRate = $event"
          />
        </div>
        <FieldInput v-model="pkg.note" label="Nota" placeholder="Ideal para ajustes puntuales." />
      </div>
    </div>

    <FieldTextarea
      v-model="form.effortBadge"
      label="Badge de esfuerzo"
      help="Aclara que requerimientos de esfuerzo medio o superior se cotizan como requerimiento independiente."
      :rows="2"
      :isSingle="true"
      class="mt-3"
    />
  </div>

  <!-- Alcance -->
  <div class="mt-4 border-t border-border-default dark:border-white/[0.08] pt-3">
    <FieldInput v-model="form.scopeTitle" label="Título de alcance" />
    <FieldTextarea
      v-model="form.scopeParagraphs"
      label="Párrafos de alcance (uno por línea)"
      help="Cláusula que aclara que lo no descrito en el alcance no hace parte del trabajo aprobado."
      :rows="6"
      :isSingle="true"
      class="mt-2"
    />
  </div>
</template>

<script setup>
import { FieldInput, FieldTextarea } from './fields.js';

const props = defineProps({
  form: { type: Object, required: true },
  proposalData: { type: Object, default: () => ({}) },
});

function addPackage() {
  if (!Array.isArray(props.form.packages)) props.form.packages = [];
  props.form.packages.push({ name: '', hours: '', discountPercent: 0, note: '', hourlyRate: '' });
}

function removePackage(idx) {
  props.form.packages.splice(idx, 1);
}
</script>
