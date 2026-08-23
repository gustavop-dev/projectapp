<template>
  <fieldset>
    <legend class="mb-2 text-xs font-medium text-text-muted">Tipos de correo</legend>
    <div class="grid gap-2 sm:grid-cols-2">
      <label
        v-for="option in options"
        :key="option.value"
        class="flex cursor-pointer items-start gap-2 rounded-lg border border-border-muted bg-surface px-3 py-2 text-xs text-text-default"
      >
        <input
          type="checkbox"
          class="mt-0.5 rounded border-border-default text-text-brand focus:ring-focus-ring"
          :checked="modelValue.includes(option.value)"
          :data-testid="`${testPrefix}-${option.value}`"
          @change="toggle(option.value)"
        >
        <span>{{ option.label }}</span>
      </label>
    </div>
  </fieldset>
</template>

<script setup>
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  testPrefix: { type: String, required: true },
});

const emit = defineEmits(['update:modelValue']);

function toggle(value) {
  const selected = new Set(props.modelValue);
  if (selected.has(value)) selected.delete(value);
  else selected.add(value);
  emit(
    'update:modelValue',
    props.options.map(option => option.value).filter(item => selected.has(item)),
  );
}
</script>
