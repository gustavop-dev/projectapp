<script setup>
import { computed, ref, watch } from 'vue';
import { useCommunicationsStore } from '~/stores/communications';
import { folderOptions } from '~/utils/communicationFolders';
const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  clientId: { type: [String, Number], default: null },
  projectId: { type: [String, Number], default: null },
});
const emit = defineEmits(['update:modelValue']);
const { t } = useI18n();
const store = useCommunicationsStore();
const folders = ref([]);
const error = ref('');
let requestVersion = 0;
const options = computed(() => [
  { value: '', label: t('communicationFiling.unfiled') },
  ...folderOptions(folders.value, { client: props.clientId, project: props.projectId }),
]);
async function load() {
  const version = ++requestVersion;
  error.value = '';
  folders.value = [];
  if (!props.clientId) return;
  const result = await store.fetchFolders({ client: props.clientId });
  if (version !== requestVersion) return;
  if (!result.success) { error.value = result.message; return; }
  folders.value = result.data;
}
watch(() => props.clientId, load, { immediate: true });
watch(options, (available) => {
  if (folders.value.length && props.modelValue && !available.some((item) => item.value === String(props.modelValue))) emit('update:modelValue', '');
});
</script>
<template>
  <BaseFormField :label="t('communicationFiling.location')">
    <BaseSelect :model-value="modelValue" :options="options" data-testid="communication-folder-picker" @update:model-value="$emit('update:modelValue', $event)" />
    <BaseAlert v-if="error" variant="danger">{{ error }}<BaseButton variant="link" @click="load">{{ t('communicationFiling.retry') }}</BaseButton></BaseAlert>
  </BaseFormField>
</template>
