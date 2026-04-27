<template>
  <form class="space-y-4" @submit.prevent="$emit('submit')">
    <div class="grid gap-4 md:grid-cols-2">
      <label class="block">
        <span class="text-sm font-medium text-text-default">Inversión</span>
        <input
          type="number"
          step="0.01"
          class="mt-1 w-full border rounded px-3 py-2"
          :value="modelValue.investment_amount"
          @input="update('investment_amount', $event.target.value)"
        />
      </label>
      <label class="block">
        <span class="text-sm font-medium text-text-default">Moneda</span>
        <select
          class="mt-1 w-full border rounded px-3 py-2"
          :value="modelValue.currency"
          @change="update('currency', $event.target.value)"
        >
          <option value="COP">COP</option>
          <option value="USD">USD</option>
        </select>
      </label>
      <label class="block">
        <span class="text-sm font-medium text-text-default">% inicial</span>
        <input
          type="number"
          min="0"
          max="100"
          class="mt-1 w-full border rounded px-3 py-2"
          :value="payment.initial_pct"
          @input="updatePayment('initial_pct', $event.target.value)"
        />
      </label>
      <label class="block">
        <span class="text-sm font-medium text-text-default">% final</span>
        <input
          type="number"
          min="0"
          max="100"
          class="mt-1 w-full border rounded px-3 py-2"
          :value="payment.final_pct"
          @input="updatePayment('final_pct', $event.target.value)"
        />
      </label>
      <label class="block md:col-span-2">
        <span class="text-sm font-medium text-text-default">Duración (texto)</span>
        <input
          type="text"
          class="mt-1 w-full border rounded px-3 py-2"
          placeholder="Ej: 1 semana"
          :value="modelValue.duration_label"
          @input="update('duration_label', $event.target.value)"
        />
      </label>
    </div>
    <div class="text-right">
      <button
        type="submit"
        class="px-4 py-2 bg-primary text-white rounded hover:bg-primary-strong"
        :disabled="busy"
      >Guardar pricing</button>
    </div>
  </form>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: { type: Object, required: true },
  busy: { type: Boolean, default: false },
});
const emit = defineEmits(['update:modelValue', 'submit']);

const payment = computed(() => props.modelValue.payment_terms || {});

function update(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value });
}
function updatePayment(key, value) {
  const next = { ...payment.value, [key]: Number(value) || 0 };
  emit('update:modelValue', { ...props.modelValue, payment_terms: next });
}
</script>
