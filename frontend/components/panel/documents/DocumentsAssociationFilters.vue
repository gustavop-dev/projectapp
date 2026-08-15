<script setup>
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import ProjectSelect from '~/components/accounting/ProjectSelect.vue';

/**
 * Filtros de asociación del listado de documentos.
 *
 * Cliente y proyecto son ejes independientes (sin cascada — eso es cosa del
 * formulario), cada uno con su recorte «sin asociar» como chip excluyente del
 * valor elegido: los documentos sueltos son un corte de primera clase, no un
 * residuo. Los valores viajan como los ejes del composable de URL:
 * null (sin filtro) | 'none' | id.
 */
const props = defineProps({
  client: { type: [Number, String], default: null },
  project: { type: [Number, String], default: null },
  /** Label del cliente activo, para rehidratar el autocomplete en deep links. */
  clientLabel: { type: String, default: '' },
});

const emit = defineEmits(['update:client', 'update:project']);

function onClientSelect(clientRow) {
  emit('update:client', clientRow ? clientRow.id : null);
}

function toggleClientNone() {
  emit('update:client', props.client === 'none' ? null : 'none');
}

function onProjectPicked(value) {
  emit('update:project', value ?? null);
}

function toggleProjectNone() {
  emit('update:project', props.project === 'none' ? null : 'none');
}
</script>

<template>
  <div class="flex flex-wrap items-end gap-3">
    <div class="flex-1 min-w-[14rem]">
      <label class="block text-sm font-medium text-text-default mb-1">Cliente</label>
      <ClientAutocomplete
        :key="client === 'none' ? 'client-none' : 'client-picker'"
        :model-value="typeof client === 'number' ? client : null"
        :initial-label="clientLabel"
        :show-linked-hint="false"
        placeholder="Filtrar por cliente..."
        test-id="documents-filter-client"
        @select="onClientSelect"
      />
    </div>
    <!-- design-tokens: allow-raw-button -->
    <button
      type="button"
      class="px-3 py-2.5 rounded-xl text-sm border transition-colors flex-shrink-0"
      :class="client === 'none'
        ? 'bg-primary-soft text-text-brand border-focus-ring/40 font-medium'
        : 'bg-surface-raised text-text-muted border-border-default hover:text-text-default'"
      data-testid="documents-filter-client-none"
      :aria-pressed="client === 'none'"
      @click="toggleClientNone"
    >
      Sin cliente
    </button>
    <div class="flex-1 min-w-[14rem]">
      <ProjectSelect
        :model-value="typeof project === 'number' ? project : null"
        :client-profile-id="typeof client === 'number' ? client : null"
        :allow-no-client="true"
        :allow-create="false"
        testid="documents-filter-project"
        @update:model-value="onProjectPicked"
      />
    </div>
    <!-- design-tokens: allow-raw-button -->
    <button
      type="button"
      class="px-3 py-2.5 rounded-xl text-sm border transition-colors flex-shrink-0"
      :class="project === 'none'
        ? 'bg-primary-soft text-text-brand border-focus-ring/40 font-medium'
        : 'bg-surface-raised text-text-muted border-border-default hover:text-text-default'"
      data-testid="documents-filter-project-none"
      :aria-pressed="project === 'none'"
      @click="toggleProjectNone"
    >
      Sin proyecto
    </button>
  </div>
</template>
