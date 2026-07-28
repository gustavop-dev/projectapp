<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <FieldInput v-model="form.index" label="Índice" placeholder="17" />
    <FieldInput v-model="form.title" label="Título" />
  </div>

  <!-- Paquetes de horas -->
  <div class="mt-2">
    <FieldInput v-model="form.packagesTitle" label="Título de los paquetes" />
    <FieldTextarea v-model="form.packagesIntro" label="Intro de los paquetes" :rows="2" :isSingle="true" class="mt-2" />

    <div class="mt-3">
      <span class="block text-xs text-text-muted mb-1">Fuente de los paquetes de horas</span>
      <BaseSegmented v-model="form.hourPackagesMode" :options="MODE_OPTIONS" size="sm" />
      <p data-testid="hour-packages-mode-hint" class="text-[11px] text-text-subtle mt-1">
        <template v-if="isAuto">
          El PDF toma los paquetes, la tarifa y la moneda del catálogo de paquetes de horas en cada
          generación. Lo que ves aquí es la última foto guardada, solo informativa.
        </template>
        <template v-else>
          Esta propuesta usa sus propios paquetes y tarifas: los cambios del catálogo no la afectan.
          La tarifa base se aplica a los paquetes sin tarifa propia.
        </template>
      </p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-3">
      <FieldCurrency
        :modelValue="form.hourlyRate"
        label="Tarifa base por hora"
        :decimals="rateDecimals"
        placeholder="30000"
        :disabled="isAuto"
        @update:modelValue="form.hourlyRate = $event"
      />
      <label class="block">
        <span class="block text-xs text-text-muted mb-0.5">Moneda</span>
        <select
          v-model="form.currency"
          :disabled="isAuto"
          class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text rounded-lg text-sm focus:ring-1 focus:ring-focus-ring/30 focus:border-focus-ring outline-none disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <option value="COP">COP</option>
          <option value="USD">USD</option>
        </select>
      </label>
    </div>

    <button
      v-if="!isAuto"
      type="button"
      data-testid="apply-base-rate-all"
      class="mt-2 text-xs font-medium text-text-brand hover:underline"
      @click="applyBaseRateToAll"
    >
      Aplicar tarifa base a todos los paquetes
    </button>

    <div class="mt-3 space-y-3">
      <div class="flex items-center justify-between">
        <label class="block text-xs font-medium text-text-muted uppercase tracking-wider">Paquetes</label>
        <button
          type="button"
          class="text-xs font-medium text-text-brand hover:underline disabled:opacity-50 disabled:cursor-not-allowed disabled:no-underline"
          :disabled="isAuto"
          @click="addPackage"
        >
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
          <button
            type="button"
            class="text-[11px] text-text-subtle hover:text-danger-strong disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="isAuto"
            @click="removePackage(idx)"
          >
            Quitar
          </button>
        </div>
        <FieldInput v-model="pkg.name" label="Nombre" placeholder="Paquete Ágil" :disabled="isAuto" />
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <FieldInput
            :modelValue="pkg.hours"
            label="Horas"
            placeholder="20"
            :disabled="isAuto"
            @update:modelValue="pkg.hours = $event"
          />
          <FieldInput
            :modelValue="pkg.discountPercent"
            label="Descuento %"
            placeholder="0"
            :disabled="isAuto"
            @update:modelValue="pkg.discountPercent = $event"
          />
          <FieldCurrency
            :modelValue="pkg.hourlyRate"
            label="Tarifa/h (opcional)"
            :decimals="rateDecimals"
            placeholder="Usa la tarifa base"
            :disabled="isAuto"
            @update:modelValue="pkg.hourlyRate = $event"
          />
        </div>
        <FieldInput v-model="pkg.note" label="Nota" placeholder="Ideal para ajustes puntuales." :disabled="isAuto" />
        <p v-if="!isAuto" :data-testid="`hour-package-preview-${idx}`" class="text-[11px] text-text-subtle">
          {{ packagePreview(pkg) }}
        </p>
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
import { computed } from 'vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import { effectiveRate, totalPrice, formatPackageMoney } from '~/utils/hourPackagePricing.js';
import { FieldCurrency, FieldInput, FieldTextarea } from './fields.js';

const props = defineProps({
  form: { type: Object, required: true },
  proposalData: { type: Object, default: () => ({}) },
});

const MODE_OPTIONS = [
  { value: 'auto', label: 'Automático (catálogo)', testId: 'hour-packages-mode-auto' },
  { value: 'manual', label: 'Manual', testId: 'hour-packages-mode-manual' },
];

const isAuto = computed(() => props.form.hourPackagesMode !== 'manual');

// COP shows whole pesos; USD keeps cents (mirrors BaseCurrencyInput usage).
const rateDecimals = computed(() => (props.form.currency === 'COP' ? 0 : 2));

function addPackage() {
  if (!Array.isArray(props.form.packages)) props.form.packages = [];
  props.form.packages.push({ name: '', hours: '', discountPercent: 0, note: '', hourlyRate: '' });
}

function removePackage(idx) {
  props.form.packages.splice(idx, 1);
}

// Empty per-package rates fall back to the section base rate at render time,
// so clearing them is the flat "apply to all" of the catalog module.
function applyBaseRateToAll() {
  for (const pkg of props.form.packages || []) pkg.hourlyRate = '';
}

// Pricing utils speak the catalog's snake_case shape; adapt with the same
// fallback the PDF applies (per-package rate, else section base rate).
function packagePreview(pkg) {
  const hasOwnRate = !(pkg.hourlyRate === '' || pkg.hourlyRate == null);
  const snake = {
    hourly_rate: hasOwnRate ? Number(pkg.hourlyRate) : Number(props.form.hourlyRate) || 0,
    discount_percent: Number(pkg.discountPercent) || 0,
    hours: Number(pkg.hours) || 0,
  };
  const currency = props.form.currency || 'COP';
  const rate = formatPackageMoney(effectiveRate(snake), currency);
  const total = formatPackageMoney(totalPrice(snake), currency);
  return `Tarifa efectiva: ${rate}/h · Total: ${total}`;
}
</script>
