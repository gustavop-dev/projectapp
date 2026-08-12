<template>
  <div>
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-light text-text-default">Linktrees</h1>
        <p class="text-sm text-text-subtle mt-1">
          Páginas de links personalizables con URL propia (/lk/@handle) — usalas como destino de las tarjetas QR.
        </p>
      </div>
      <BaseButton variant="primary" size="sm" data-testid="linktree-new" @click="openCreateModal">
        Nuevo linktree
      </BaseButton>
    </div>

    <div v-if="store.isLoading && store.linktrees.length === 0" class="text-center py-16 text-text-subtle text-sm">
      Cargando linktrees...
    </div>

    <BaseEmptyState
      v-else-if="store.linktrees.length === 0"
      title="Sin linktrees todavía"
      description="Creá tu primer linktree para usarlo como destino de una tarjeta QR."
    />

    <div v-else class="bg-surface border border-border-default rounded-xl shadow-card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-surface-raised">
          <tr>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Nombre</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">URL pública</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Tipo</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Botones</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Activo</th>
            <th class="text-right px-4 py-3 font-semibold text-text-muted">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border-muted">
          <tr v-for="tree in store.linktrees" :key="tree.id" :data-testid="`linktree-row-${tree.id}`">
            <td class="px-4 py-3 text-text-default">{{ tree.name }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <code class="text-xs bg-surface-muted rounded px-2 py-1">{{ publicLinkFor(tree) }}</code>
                <BaseButton variant="ghost" size="sm" icon-only aria-label="Copiar link" @click="copyLink(tree)">
                  <ClipboardIcon class="h-4 w-4" />
                </BaseButton>
              </div>
            </td>
            <td class="px-4 py-3 text-text-muted">{{ tree.kind === 'company' ? 'Empresa' : 'Personal' }}</td>
            <td class="px-4 py-3 text-text-muted">{{ tree.buttons_count }}</td>
            <td class="px-4 py-3">
              <BaseToggle
                :model-value="tree.is_active"
                :aria-label="`Activar ${tree.name}`"
                :data-testid="`linktree-toggle-${tree.id}`"
                @update:model-value="(value) => onToggleActive(tree, value)"
              />
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-end gap-2">
                <BaseButton
                  variant="ghost"
                  size="sm"
                  :data-testid="`linktree-edit-${tree.id}`"
                  @click="navigateTo(lp(`/panel/linktrees/${tree.id}/edit`))"
                >
                  Editar
                </BaseButton>
                <BaseButton
                  variant="danger-ghost"
                  size="sm"
                  icon-only
                  aria-label="Eliminar linktree"
                  :data-testid="`linktree-delete-${tree.id}`"
                  @click="onDelete(tree)"
                >
                  <TrashIcon class="h-4 w-4" />
                </BaseButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create modal -->
    <BaseModal v-model="formModal.open" size="md" padding="md">
      <form data-testid="linktree-form" @submit.prevent="onSubmit">
        <h3 class="text-lg font-bold text-text-default mb-4">Nuevo linktree</h3>

        <div class="space-y-4">
          <BaseFormField label="Nombre interno" for="linktree-name" required :error="formErrors.name">
            <BaseInput id="linktree-name" v-model="formModal.name" data-testid="linktree-name-input" />
          </BaseFormField>

          <BaseFormField
            label="Handle"
            for="linktree-handle"
            required
            hint="La URL pública queda como /lk/@handle — minúsculas, números, punto, guion y guion bajo."
            :error="formErrors.handle"
          >
            <BaseInput
              id="linktree-handle"
              v-model="formModal.handle"
              placeholder="@mi_handle"
              data-testid="linktree-handle-input"
            />
          </BaseFormField>

          <BaseFormField label="Tipo" for="linktree-kind">
            <BaseSegmented
              id="linktree-kind"
              v-model="formModal.kind"
              :options="[
                { value: 'personal', label: 'Personal' },
                { value: 'company', label: 'Empresa' },
              ]"
            />
          </BaseFormField>
        </div>

        <div class="flex items-center justify-end gap-2 mt-6">
          <BaseButton type="button" variant="ghost" size="sm" @click="formModal.open = false">Cancelar</BaseButton>
          <BaseButton type="submit" variant="primary" size="sm" :loading="store.isUpdating" data-testid="linktree-save">
            Crear y editar
          </BaseButton>
        </div>
      </form>
    </BaseModal>

    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue';
import { ClipboardIcon, TrashIcon } from '@heroicons/vue/24/outline';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { useLinktreesStore } from '~/stores/linktrees';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const store = useLinktreesStore();
const notify = usePanelNotify();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();
const localePath = useLocalePath();
const lp = (path) => localePath(path);

const formModal = reactive({ open: false, name: '', handle: '', kind: 'personal' });
const formErrors = reactive({ name: '', handle: '' });

onMounted(() => {
  store.fetchLinktrees();
});

function publicLinkFor(tree) {
  return `${window.location.origin}${tree.public_path}`;
}

async function copyLink(tree) {
  try {
    await navigator.clipboard.writeText(publicLinkFor(tree));
    notify.success({ title: 'Link copiado' });
  } catch {
    notify.error({ title: 'No se pudo copiar', detail: 'Copiá el link manualmente.' });
  }
}

function openCreateModal() {
  formModal.name = '';
  formModal.handle = '';
  formModal.kind = 'personal';
  formErrors.name = '';
  formErrors.handle = '';
  formModal.open = true;
}

async function onToggleActive(tree, value) {
  const result = await store.updateLinktree(tree.id, { is_active: value });
  if (!result.success) {
    notify.error({ title: 'No se pudo actualizar el linktree' });
  }
}

async function onSubmit() {
  formErrors.name = '';
  formErrors.handle = '';
  const result = await store.createLinktree({
    name: formModal.name,
    handle: formModal.handle,
    kind: formModal.kind,
  });

  if (!result.success) {
    formErrors.name = result.errors?.name?.[0] || '';
    formErrors.handle = result.errors?.handle?.[0] || '';
    if (!result.errors) {
      notify.error({ title: 'No se pudo crear el linktree' });
    }
    return;
  }
  formModal.open = false;
  navigateTo(lp(`/panel/linktrees/${result.data.id}/edit`));
}

async function onDelete(tree) {
  const confirmed = await requestConfirm({
    title: 'Eliminar linktree',
    message: `"${tree.name}" se eliminará de forma permanente. Las tarjetas QR que lo usen como destino quedarán sin configurar hasta que les asignes otro. Esta acción no se puede deshacer.`,
    confirmText: 'Eliminar',
    variant: 'danger',
  });
  if (!confirmed) return;

  const result = await store.deleteLinktree(tree.id);
  if (!result.success) {
    notify.error({ title: 'No se pudo eliminar el linktree' });
  }
}
</script>
