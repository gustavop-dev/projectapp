<template>
  <div class="space-y-4" data-testid="communication-settings-panel">
    <div class="flex flex-col gap-3 rounded-xl border border-border-muted bg-surface p-4 panel-portrait:flex-row panel-portrait:items-center panel-portrait:justify-between">
      <div>
        <h2 class="text-lg font-semibold text-text-default">Configuraciones de Comunicaciones</h2>
        <p class="mt-1 text-sm text-text-subtle">
          Estas preferencias son personales y se conservan en todos tus dispositivos.
        </p>
      </div>
      <BaseButton
        variant="secondary"
        size="md"
        data-testid="communication-settings-back"
        @click="requestClose"
      >
        <BaseActionIcon action="back" />
        Volver a los hilos
      </BaseButton>
    </div>

    <BaseAlert v-if="store.preferenceError" variant="danger">
      {{ store.preferenceError }} Los hilos siguen disponibles con valores seguros.
    </BaseAlert>

    <BaseAlert v-if="isDirty" variant="warning" data-testid="communication-settings-unsaved">
      Tienes cambios sin guardar.
    </BaseAlert>

    <section class="rounded-xl border border-border-muted bg-surface p-5 shadow-card panel-portrait:p-6">
      <h3 class="text-base font-semibold text-text-default">Organización del listado</h3>
      <p class="mt-1 text-sm text-text-muted">
        Una URL o vista guardada explícita siempre tiene prioridad sobre estos valores.
      </p>

      <div class="mt-5 grid gap-5 panel-landscape:grid-cols-2">
        <BaseFormField label="Navegar inicialmente por">
          <BaseSegmented
            v-model="draft.navigation_mode"
            :options="NAVIGATION_OPTIONS"
            full-width
            data-testid="communication-settings-navigation-mode"
          />
        </BaseFormField>

        <BaseFormField label="Orden inicial">
          <BaseSegmented
            v-model="draft.thread_order"
            :options="ORDER_OPTIONS"
            full-width
            data-testid="communication-settings-order"
          />
        </BaseFormField>

        <BaseFormField label="Hilos por página">
          <BaseSegmented
            v-model="draft.page_size"
            :options="PAGE_SIZE_OPTIONS"
            full-width
            data-testid="communication-settings-page-size"
          />
        </BaseFormField>

        <BaseFormField label="Ancho de la navegación lateral">
          <BaseSegmented
            v-model="draft.navigation_width"
            :options="WIDTH_OPTIONS"
            full-width
            data-testid="communication-settings-navigation-width"
          />
          <p class="mt-2 text-xs text-text-subtle">
            El ajuste manual desde el listado puede conservar cualquier ancho entre 240 y 400 px.
          </p>
        </BaseFormField>
      </div>
    </section>

    <section class="rounded-xl border border-border-muted bg-surface p-5 shadow-card panel-portrait:p-6">
      <h3 class="text-base font-semibold text-text-default">Registro de mensajes</h3>
      <p class="mt-1 text-sm text-text-muted">
        Sólo define el punto de partida; las respuestas y ediciones conservan su canal original.
      </p>

      <div class="mt-5 grid gap-5 panel-landscape:grid-cols-2">
        <BaseFormField label="Canal inicial para mensajes nuevos">
          <BaseSegmented
            v-model="draft.default_channel"
            :options="CHANNEL_OPTIONS"
            full-width
            data-testid="communication-settings-default-channel"
          />
        </BaseFormField>

        <div class="flex items-center justify-between gap-4 rounded-xl border border-border-muted p-4">
          <div>
            <p class="text-sm font-medium text-text-default">Mostrar ayuda del registro manual</p>
            <p class="mt-1 text-xs text-text-subtle">Mantiene visible la explicación al entrar al módulo.</p>
          </div>
          <BaseToggle
            v-model="draft.show_manual_help"
            aria-label="Mostrar ayuda del registro manual"
            data-testid="communication-settings-show-help"
          />
        </div>
      </div>
    </section>

    <div class="flex flex-col-reverse gap-2 panel-portrait:flex-row panel-portrait:justify-end">
      <BaseButton
        variant="secondary"
        size="md"
        :disabled="!isDirty || store.isPreferenceSaving"
        data-testid="communication-settings-cancel"
        @click="resetDraft"
      >
        Descartar cambios
      </BaseButton>
      <BaseButton
        variant="primary"
        size="md"
        :disabled="!isDirty"
        :loading="store.isPreferenceSaving"
        data-testid="communication-settings-save"
        @click="save"
      >
        Guardar configuraciones
      </BaseButton>
    </div>

    <ViewSettingsPanel
      :filter-views="[{ value: 'communication', label: 'Comunicaciones' }]"
      @reset="$emit('reset-tabs')"
    />

    <section class="rounded-xl border border-danger-strong/30 bg-surface p-5 shadow-card panel-portrait:p-6">
      <h3 class="text-base font-semibold text-text-default">Restablecer preferencias</h3>
      <p class="mt-1 text-sm text-text-muted">
        Vuelve a proyecto, recientes, 20 hilos, WhatsApp, ayuda visible y ancho estándar.
        Las vistas propias no se eliminan.
      </p>
      <BaseButton
        variant="danger"
        size="sm"
        class="mt-4"
        data-testid="communication-settings-reset"
        @click="resetConfirmOpen = true"
      >
        Restablecer preferencias
      </BaseButton>
    </section>

    <ConfirmModal
      v-model="discardConfirmOpen"
      title="Descartar cambios"
      message="Los cambios sin guardar se perderán y volverás al listado de hilos."
      confirm-text="Descartar y volver"
      cancel-text="Continuar editando"
      variant="danger"
      @confirm="discardAndClose"
    />

    <ConfirmModal
      v-model="resetConfirmOpen"
      title="Restablecer preferencias"
      message="Se recuperarán los valores iniciales del módulo. Tus vistas guardadas se conservarán."
      confirm-text="Restablecer"
      cancel-text="Cancelar"
      variant="danger"
      @confirm="resetPreferences"
    />

    <ConfirmModal
      v-model="leaveConfirmState.open"
      :title="leaveConfirmState.title"
      :message="leaveConfirmState.message"
      :confirm-text="leaveConfirmState.confirmText"
      :cancel-text="leaveConfirmState.cancelText"
      :variant="leaveConfirmState.variant"
      :require-type-text="leaveConfirmState.requireTypeText"
      :hide-cancel="leaveConfirmState.hideCancel"
      :secondary-text="leaveConfirmState.secondaryText"
      :secondary-variant="leaveConfirmState.secondaryVariant"
      :secondary-hint="leaveConfirmState.secondaryHint"
      :loading="leaveConfirmState.busy"
      @confirm="handleLeaveConfirmed"
      @secondary="handleLeaveSecondary"
      @cancel="handleLeaveCancelled"
    />
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import ViewSettingsPanel from '~/components/panel/ViewSettingsPanel.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useUnsavedGuard } from '~/composables/useUnsavedGuard';
import { useCommunicationsStore } from '~/stores/communications';

const emit = defineEmits(['close', 'reset-tabs']);
const store = useCommunicationsStore();
const notify = usePanelNotify();

const NAVIGATION_OPTIONS = [
  { value: 'project', label: 'Proyectos' },
  { value: 'client', label: 'Clientes' },
];
const ORDER_OPTIONS = [
  { value: 'recent', label: 'Recientes' },
  { value: 'oldest', label: 'Antiguos' },
  { value: 'title', label: 'A–Z' },
];
const PAGE_SIZE_OPTIONS = [
  { value: 10, label: '10' },
  { value: 20, label: '20' },
  { value: 50, label: '50' },
];
const WIDTH_OPTIONS = [
  { value: 240, label: 'Compacto' },
  { value: 288, label: 'Estándar' },
  { value: 400, label: 'Amplio' },
];
const CHANNEL_OPTIONS = [
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'email', label: 'Correo' },
];

const draft = reactive({ ...store.preferences });
const saved = ref({ ...store.preferences });
const discardConfirmOpen = ref(false);
const resetConfirmOpen = ref(false);

const dirtyPayload = computed(() => Object.fromEntries(
  Object.entries(draft).filter(([key, value]) => value !== saved.value[key]),
));
const isDirty = computed(() => Object.keys(dirtyPayload.value).length > 0);
const {
  confirmState: leaveConfirmState,
  handleConfirmed: handleLeaveConfirmed,
  handleSecondaryAction: handleLeaveSecondary,
  handleCancelled: handleLeaveCancelled,
} = useUnsavedGuard({
  flags: { preferences: () => isDirty.value },
  labels: { preferences: 'configuraciones de Comunicaciones' },
  save,
});

watch(
  () => store.preferences,
  (preferences) => sync(preferences, { preserveDirty: true }),
  { deep: true },
);

function sync(preferences, { preserveDirty = false } = {}) {
  const pending = preserveDirty ? { ...dirtyPayload.value } : {};
  Object.assign(draft, preferences, pending);
  saved.value = { ...preferences };
}

function resetDraft() {
  Object.assign(draft, saved.value);
}

async function save() {
  if (!isDirty.value) return true;
  const result = await store.updatePreferences(dirtyPayload.value);
  if (!result.success) return false;
  sync(result.data);
  notify.success({ title: 'Configuraciones guardadas' });
  return true;
}

async function resetPreferences() {
  const result = await store.resetPreferences();
  if (!result.success) return;
  sync(result.data);
  notify.success({ title: 'Preferencias restablecidas' });
}

function requestClose() {
  if (isDirty.value) {
    discardConfirmOpen.value = true;
    return;
  }
  emit('close');
}

function discardAndClose() {
  resetDraft();
  emit('close');
}

defineExpose({ requestClose });
</script>
