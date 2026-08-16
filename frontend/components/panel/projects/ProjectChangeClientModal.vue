<template>
  <BaseModal
    :model-value="open"
    size="lg"
    title-id="project-change-client-title"
    @close="emit('close')"
  >
    <div class="px-6 pt-6 pb-2">
      <h3 id="project-change-client-title" class="text-lg font-bold text-text-default">
        Cambiar el cliente de "{{ project?.name }}"
      </h3>
      <p class="text-sm text-text-subtle mt-1">
        Elige el cliente destino y revisa el impacto completo antes de
        confirmar. Los documentos emitidos nunca se tocan.
      </p>
    </div>

    <div class="px-6 py-4 space-y-4" data-testid="project-change-client-modal">
      <ClientAutocomplete
        v-model="clientId"
        test-id="project-change-client-picker"
        placeholder="Buscar el cliente destino..."
        :show-linked-hint="false"
        @select="onClientSelect"
      />

      <BaseAlert
        v-if="errorMessage"
        variant="warning"
        data-testid="project-change-client-error"
      >
        {{ errorMessage }}
      </BaseAlert>

      <p v-if="isLoadingPreview" class="text-sm text-text-subtle">
        Calculando el impacto...
      </p>

      <template v-if="preview && !isLoadingPreview">
        <div
          class="rounded-lg border border-border-muted bg-surface-muted divide-y divide-border-muted"
          data-testid="project-change-client-preview"
        >
          <section v-if="movable.length" class="px-3 py-2">
            <p class="text-xs font-semibold uppercase tracking-wide text-text-subtle mb-1">
              Registros del proyecto ({{ movable.length }})
            </p>
            <ul class="text-xs text-text-default space-y-0.5 max-h-40 overflow-y-auto">
              <li v-for="row in movable" :key="`m-${row.entity}-${row.id}`" class="truncate">
                {{ row.label }}
              </li>
            </ul>
          </section>
          <section
            v-if="preview.incomes_blocked.length"
            class="px-3 py-2"
            data-testid="project-change-client-blocked"
          >
            <p class="text-xs font-semibold text-text-default mb-1">
              Con cuenta de cobro activa ({{ preview.incomes_blocked.length }}):
              se desvinculan del proyecto y conservan su cliente.
            </p>
            <ul class="text-xs text-text-muted space-y-0.5 max-h-24 overflow-y-auto">
              <li v-for="row in preview.incomes_blocked" :key="`b-${row.id}`" class="truncate">
                {{ row.label }} · {{ row.period_label }}
              </li>
            </ul>
          </section>
          <section v-if="preview.draft_accounts.length" class="px-3 py-2">
            <p class="text-xs font-semibold uppercase tracking-wide text-text-subtle mb-1">
              Borradores de cuenta ({{ preview.draft_accounts.length }})
            </p>
            <ul class="text-xs text-text-muted space-y-0.5">
              <li v-for="row in preview.draft_accounts" :key="`d-${row.id}`" class="truncate">
                {{ row.public_number || row.title }}
              </li>
            </ul>
          </section>
          <section
            v-if="preview.issued_accounts.length"
            class="px-3 py-2"
            data-testid="project-change-client-issued"
          >
            <p class="text-xs font-semibold text-text-default mb-1">
              Emitidas ({{ preview.issued_accounts.length }}): no se reasignan.
              Si hubo un error, anula y emite una nueva.
            </p>
            <ul class="text-xs text-text-muted space-y-0.5">
              <li v-for="row in preview.issued_accounts" :key="`i-${row.id}`" class="truncate">
                {{ row.public_number || row.title }} · {{ row.status_label }}
              </li>
            </ul>
          </section>
          <section v-if="preview.clientless.length" class="px-3 py-2">
            <p class="text-xs text-text-muted">
              {{ preview.clientless.length }} sin cliente: quedan como están
              (complétalos luego con la asignación masiva).
            </p>
          </section>
          <section v-if="preview.other_documents_count" class="px-3 py-2">
            <p class="text-xs text-text-muted">
              {{ preview.other_documents_count }} documento(s) del proyecto lo
              acompañan sin cambios.
            </p>
          </section>
        </div>

        <!-- Sin preselección a propósito: la decisión de arrastrar o
             desvincular se toma en cada cascada, nunca por default. -->
        <BaseFormField
          label="¿Qué hacemos con los registros?"
          hint="Mover: siguen al proyecto con el nuevo cliente. Desvincular: conservan su cliente y pierden el proyecto."
        >
          <BaseSegmented
            v-model="mode"
            :options="[
              { value: 'move', label: 'Mover al nuevo cliente' },
              { value: 'detach', label: 'Desvincular del proyecto' },
            ]"
            data-testid="project-change-client-mode"
          />
        </BaseFormField>
      </template>
    </div>

    <div class="px-6 pb-6 pt-2 flex items-center justify-end gap-2">
      <BaseButton
        variant="secondary"
        size="sm"
        data-testid="project-change-client-cancel"
        @click="emit('close')"
      >
        Cancelar
      </BaseButton>
      <BaseButton
        variant="primary"
        size="sm"
        :disabled="!canConfirm"
        data-testid="project-change-client-confirm"
        @click="confirmChange"
      >
        {{ store.isUpdating ? 'Aplicando...' : 'Cambiar cliente del proyecto' }}
      </BaseButton>
    </div>
  </BaseModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import BaseAlert from '~/components/base/BaseAlert.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelProjectsStore } from '~/stores/panel_projects';

/**
 * The guided cascade for changing a project's owner — the only path (the
 * form keeps the field immutable). Pick the destination, read the full
 * impact, choose a mode EVERY time (no preselection: "preguntar cada vez"
 * is the agreed rule), confirm. A 409 means the linked set moved under the
 * open dialog: the preview reloads instead of guessing.
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  project: { type: Object, default: null },
});

const emit = defineEmits(['close', 'changed']);

const store = usePanelProjectsStore();
const notify = usePanelNotify();

const clientId = ref(null);
const clientName = ref('');
const preview = ref(null);
const mode = ref('');
const isLoadingPreview = ref(false);
const errorMessage = ref('');

const movable = computed(() => {
  if (!preview.value) return [];
  return [
    ...preview.value.hostings_move.map((row) => ({ ...row, entity: 'hosting' })),
    ...preview.value.incomes_move.map((row) => ({
      ...row,
      entity: 'income',
      label: `${row.label} · ${row.kind_label} · ${row.period_label}`,
    })),
  ];
});

const canConfirm = computed(() => Boolean(
  preview.value && mode.value && !store.isUpdating && !isLoadingPreview.value,
));

watch(() => props.open, (open) => {
  if (!open) return;
  clientId.value = null;
  clientName.value = '';
  preview.value = null;
  mode.value = '';
  errorMessage.value = '';
});

function onClientSelect(client) {
  clientName.value = client?.name || '';
}

watch(clientId, (id) => {
  preview.value = null;
  mode.value = '';
  errorMessage.value = '';
  if (id != null) loadPreview();
});

async function loadPreview() {
  isLoadingPreview.value = true;
  const result = await store.previewChangeClient(props.project.id, clientId.value);
  isLoadingPreview.value = false;
  if (!result.success) {
    errorMessage.value = result.message;
    return;
  }
  preview.value = result.data;
}

async function confirmChange() {
  errorMessage.value = '';
  const result = await store.changeClient(props.project.id, {
    client_profile_id: clientId.value,
    mode: mode.value,
    hosting_ids: preview.value.hosting_ids,
    income_ids: preview.value.income_ids,
  });
  if (result.success) {
    const { moved, detached } = result.data;
    const parts = [];
    const movedTotal = moved.hostings + moved.incomes + moved.draft_accounts;
    const detachedTotal = detached.hostings + detached.incomes + detached.draft_accounts;
    if (movedTotal) parts.push(`${movedTotal} movidos al nuevo cliente`);
    if (detachedTotal) parts.push(`${detachedTotal} desvinculados`);
    notify.success({
      title: `"${props.project.name}" ahora es de ${clientName.value}`,
      detail: parts.join(' · '),
    });
    emit('changed', result.data);
    return;
  }
  if (result.code === 'records_not_found' || result.code === 'records_changed') {
    // The linked set moved while the dialog was open; show the fresh plan.
    errorMessage.value = 'Los registros del proyecto cambiaron mientras confirmabas. Revisa el nuevo impacto.';
    mode.value = '';
    await loadPreview();
    return;
  }
  errorMessage.value = result.message;
}
</script>
