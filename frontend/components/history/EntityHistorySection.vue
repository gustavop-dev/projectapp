<script setup>
import { ref } from 'vue';
import EntityHistoryPanel from './EntityHistoryPanel.vue';
defineProps({ entityType: { type: String, required: true }, objectId: { type: [String, Number], required: true } });
const open = ref(false);
</script>
<template>
  <section class="my-4 rounded-xl border border-border-muted p-4">
    <BaseButton variant="secondary" :aria-expanded="open" data-testid="open-entity-history" @click="open = !open">{{ open ? 'Cerrar historial' : 'Ver historial de cambios' }}</BaseButton>
    <EntityHistoryPanel v-if="open" class="mt-4" :entity-type="entityType" :object-id="objectId" />
  </section>
</template>
