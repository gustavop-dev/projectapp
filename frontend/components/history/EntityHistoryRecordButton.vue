<script setup>
import { ref } from 'vue';
import EntityHistoryRecordModal from './EntityHistoryRecordModal.vue';
defineProps({ entityType: { type: String, required: true }, record: { type: Object, required: true } });
const open = ref(false);
</script>
<template>
  <BaseButton variant="secondary" size="sm" data-testid="history-record-open" @click.stop="open = true">Detalle e historial</BaseButton>
  <EntityHistoryRecordModal :open="open" :entity-type="entityType" :record="record" @close="open = false" />
</template>
