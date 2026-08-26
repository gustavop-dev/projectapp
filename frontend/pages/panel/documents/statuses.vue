<script setup>
import StateCatalogManager from '~/components/panel/states/StateCatalogManager.vue';
import { useDocumentStateStore } from '~/stores/document_states';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });
useHead({ title: 'Estados de documentos | ProjectApp' });

const stateStore = useDocumentStateStore();
</script>

<template>
  <StateCatalogManager
    :state-store="stateStore"
    title="Estados de documentos"
    description="Administra el ciclo, las señales, sus colores y las reglas de exclusión. Los episodios históricos nunca se borran."
    back-to="/panel/documents"
    back-label="Volver a documentos"
    test-id="document-state-catalog"
    active-count-field="active_document_count"
    active-count-label="documentos"
    manage-groups
  />
</template>
