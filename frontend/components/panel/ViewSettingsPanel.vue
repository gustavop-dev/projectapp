<template>
  <div class="space-y-4" data-testid="view-settings-panel">
    <section class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6">
      <h2 class="text-lg font-bold text-text-default mb-1">Pestañas de filtros guardados</h2>
      <p class="text-sm text-text-muted mb-5">
        Restaura las pestañas predefinidas de esta vista. Al restablecer se
        eliminan tus pestañas personalizadas.
      </p>
      <div class="space-y-2">
        <div
          v-for="view in filterViews"
          :key="view.value"
          class="flex items-center justify-between gap-3"
        >
          <span class="text-sm text-text-default">{{ view.label }}</span>
          <BaseButton
            variant="secondary"
            size="sm"
            :disabled="resettingView !== null"
            :data-testid="`view-settings-reset-tabs-${view.value}`"
            @click="askResetTabs(view)"
          >
            {{ resettingView === view.value ? 'Restableciendo...' : 'Restablecer' }}
          </BaseButton>
        </div>
      </div>
    </section>

    <slot />

    <ConfirmModal
      v-model="resetConfirmOpen"
      title="Restablecer pestañas"
      :message="resetConfirmMessage"
      confirm-text="Restablecer"
      cancel-text="Cancelar"
      variant="danger"
      @confirm="doResetTabs"
      @cancel="pendingResetView = null"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { create_request } from '~/stores/services/request_http';

const props = defineProps({
  // SavedFilterTab views this panel can reset: [{ value, label }].
  filterViews: { type: Array, required: true },
});

const emit = defineEmits(['reset']);

const notify = usePanelNotify();

const resetConfirmOpen = ref(false);
const pendingResetView = ref(null);
const resettingView = ref(null);

const resetConfirmMessage = computed(() =>
  pendingResetView.value
    ? `Se eliminarán tus pestañas personalizadas de "${pendingResetView.value.label}" ` +
      'y se restaurarán las predefinidas. Esta acción no se puede deshacer.'
    : '',
);

function askResetTabs(view) {
  pendingResetView.value = view;
  resetConfirmOpen.value = true;
}

async function doResetTabs() {
  const view = pendingResetView.value;
  if (!view) return;
  resettingView.value = view.value;
  try {
    await create_request('accounts/saved-filter-tabs/reset/', { view: view.value });
    notify.success({
      title: 'Pestañas restablecidas',
      detail: `La vista ${view.label} volvió a sus filtros predefinidos.`,
    });
    emit('reset', view.value);
  } catch (error) {
    notify.error({
      title: 'No se pudieron restablecer las pestañas',
      detail: error?.response?.data?.view || error?.message,
    });
  } finally {
    resettingView.value = null;
    pendingResetView.value = null;
  }
}
</script>
