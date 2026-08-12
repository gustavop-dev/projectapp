<template>
  <BaseFormField :label="label" :hint="hint">
    <BaseSelect
      :model-value="modelValue ?? ''"
      :disabled="!clientProfileId || loading"
      :data-testid="testid"
      @update:model-value="onChange"
    >
      <option value="">{{ emptyLabel }}</option>
      <option v-for="project in projects" :key="project.id" :value="project.id">
        {{ project.name }}
      </option>
    </BaseSelect>
  </BaseFormField>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseSelect from '~/components/base/BaseSelect.vue';
import { useAccountingStore } from '~/stores/accounting';

/**
 * Project picker scoped to one client.
 *
 * A select rather than an autocomplete: a client has a handful of projects,
 * not a catalog. Disabled until a client is chosen, because the ownership
 * rule the backend enforces (the project must belong to the record's client)
 * cannot even be evaluated without one.
 */
const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  /** UserProfile pk of the selected client, or null. */
  clientProfileId: { type: [Number, String], default: null },
  label: { type: String, default: 'Proyecto' },
  testid: { type: String, default: 'project-select' },
});

const emit = defineEmits(['update:modelValue']);

const store = useAccountingStore();
const projects = ref([]);
const loading = ref(false);

const emptyLabel = computed(() => {
  if (!props.clientProfileId) return 'Elige un cliente primero';
  if (loading.value) return 'Cargando proyectos...';
  return projects.value.length ? 'Sin proyecto' : 'Este cliente no tiene proyectos';
});

const hint = computed(() => {
  if (!props.clientProfileId) return '';
  if (!loading.value && !projects.value.length) {
    return 'Los proyectos se crean en /panel/projects.';
  }
  // Item 3 of the requirement: an empty project is a legitimate state, not
  // pending work — a cobro por diagnóstico happens before there is one.
  return 'Opcional. Un cobro por diagnóstico todavía no tiene proyecto.';
});

async function load() {
  if (!props.clientProfileId) {
    projects.value = [];
    return;
  }
  loading.value = true;
  const result = await store.fetchProjectsForClient(props.clientProfileId);
  projects.value = result.success ? result.data : [];
  loading.value = false;
}

function onChange(value) {
  emit('update:modelValue', value === '' ? null : Number(value));
}

watch(
  () => props.clientProfileId,
  (next, previous) => {
    load();
    // The previous project belonged to the previous client; keeping it would
    // send the backend a pair it is going to reject anyway.
    if (previous !== undefined && next !== previous && props.modelValue) {
      emit('update:modelValue', null);
    }
  },
  { immediate: true },
);
</script>
