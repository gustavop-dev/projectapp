<template>
  <div>
    <div class="mb-6 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-light text-text-default">Tarjetas QR</h1>
        <p class="text-sm text-text-subtle mt-1">
          Generá códigos QR con un link corto y cambiá su destino cuando quieras, sin reimprimir nada.
        </p>
      </div>
      <BaseButton variant="primary" size="sm" data-testid="qr-card-new" @click="openCreateModal">
        Nueva tarjeta
      </BaseButton>
    </div>

    <div v-if="store.isLoading && store.cards.length === 0" class="text-center py-16 text-text-subtle text-sm">
      Cargando tarjetas...
    </div>

    <BaseEmptyState
      v-else-if="store.cards.length === 0"
      title="Sin tarjetas todavía"
      description="Creá tu primera tarjeta QR para generar un link corto."
    />

    <div v-else class="bg-surface border border-border-default rounded-xl shadow-card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-surface-raised">
          <tr>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Nombre</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Link corto</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Destino</th>
            <th class="text-left px-4 py-3 font-semibold text-text-muted">Activa</th>
            <th class="text-right px-4 py-3 font-semibold text-text-muted">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border-muted">
          <tr v-for="card in store.cards" :key="card.id" :data-testid="`qr-card-row-${card.id}`">
            <td class="px-4 py-3 text-text-default">{{ card.name }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <code class="text-xs bg-surface-muted rounded px-2 py-1">{{ shortLinkFor(card) }}</code>
                <BaseButton variant="ghost" size="sm" icon-only aria-label="Copiar link" @click="copyLink(card)">
                  <ClipboardIcon class="h-4 w-4" />
                </BaseButton>
              </div>
            </td>
            <td class="px-4 py-3 text-text-muted">
              <span v-if="card.destination_url">{{ card.destination_url }}</span>
              <span v-else class="text-text-subtle italic">Sin configurar</span>
            </td>
            <td class="px-4 py-3">
              <BaseToggle
                :model-value="card.is_active"
                :aria-label="`Activar ${card.name}`"
                :data-testid="`qr-card-toggle-${card.id}`"
                @update:model-value="(value) => onToggleActive(card, value)"
              />
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-end gap-2">
                <BaseButton variant="secondary" size="sm" :data-testid="`qr-card-download-${card.id}`" @click="openDownloadModal(card)">
                  Descargar QR
                </BaseButton>
                <BaseButton variant="ghost" size="sm" :data-testid="`qr-card-edit-${card.id}`" @click="openEditModal(card)">
                  Editar
                </BaseButton>
                <BaseButton
                  variant="danger-ghost"
                  size="sm"
                  icon-only
                  aria-label="Eliminar tarjeta"
                  :data-testid="`qr-card-delete-${card.id}`"
                  @click="onDelete(card)"
                >
                  <TrashIcon class="h-4 w-4" />
                </BaseButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / edit modal -->
    <BaseModal v-model="formModal.open" size="md">
      <form data-testid="qr-card-form" @submit.prevent="onSubmit">
        <h3 class="text-lg font-bold text-text-default mb-4">
          {{ formModal.editingId ? 'Editar tarjeta' : 'Nueva tarjeta' }}
        </h3>

        <div class="space-y-4">
          <BaseFormField label="Nombre" for="qr-card-name" required :error="formErrors.name">
            <BaseInput id="qr-card-name" v-model="formModal.name" data-testid="qr-card-name-input" />
          </BaseFormField>

          <BaseFormField
            label="Link de destino"
            for="qr-card-destination"
            hint="Opcional — podés dejarlo vacío y completarlo después."
            :error="formErrors.destination_url"
          >
            <BaseInput
              id="qr-card-destination"
              v-model="formModal.destinationUrl"
              placeholder="https://..."
              data-testid="qr-card-destination-input"
            />
          </BaseFormField>
        </div>

        <div class="flex items-center justify-end gap-2 mt-6">
          <BaseButton type="button" variant="ghost" size="sm" @click="formModal.open = false">Cancelar</BaseButton>
          <BaseButton type="submit" variant="primary" size="sm" :loading="store.isUpdating" data-testid="qr-card-save">
            Guardar
          </BaseButton>
        </div>
      </form>
    </BaseModal>

    <DownloadQrModal v-model="downloadModal.open" :card="downloadModal.card" />
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
import BaseEmptyState from '~/components/base/BaseEmptyState.vue';
import DownloadQrModal from '~/components/panel/qr-cards/DownloadQrModal.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useQrCardsStore } from '~/stores/qr_cards';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const store = useQrCardsStore();
const notify = usePanelNotify();

const formModal = reactive({ open: false, editingId: null, name: '', destinationUrl: '' });
const formErrors = reactive({ name: '', destination_url: '' });
const downloadModal = reactive({ open: false, card: null });

onMounted(() => {
  store.fetchCards();
});

function shortLinkFor(card) {
  return `${window.location.origin}/t/${card.id}/`;
}

async function copyLink(card) {
  try {
    await navigator.clipboard.writeText(shortLinkFor(card));
    notify.success({ title: 'Link copiado' });
  } catch {
    notify.error({ title: 'No se pudo copiar', detail: 'Copiá el link manualmente.' });
  }
}

function openCreateModal() {
  formModal.editingId = null;
  formModal.name = '';
  formModal.destinationUrl = '';
  formErrors.name = '';
  formErrors.destination_url = '';
  formModal.open = true;
}

function openEditModal(card) {
  formModal.editingId = card.id;
  formModal.name = card.name;
  formModal.destinationUrl = card.destination_url;
  formErrors.name = '';
  formErrors.destination_url = '';
  formModal.open = true;
}

function openDownloadModal(card) {
  downloadModal.card = card;
  downloadModal.open = true;
}

async function onToggleActive(card, value) {
  const result = await store.updateCard(card.id, { is_active: value });
  if (!result.success) {
    notify.error({ title: 'No se pudo actualizar la tarjeta' });
  }
}

async function onSubmit() {
  formErrors.name = '';
  formErrors.destination_url = '';
  const payload = { name: formModal.name, destination_url: formModal.destinationUrl };
  const result = formModal.editingId
    ? await store.updateCard(formModal.editingId, payload)
    : await store.createCard(payload);

  if (!result.success) {
    formErrors.name = result.errors?.name?.[0] || '';
    formErrors.destination_url = result.errors?.destination_url?.[0] || '';
    if (!result.errors) {
      notify.error({ title: 'No se pudo guardar la tarjeta' });
    }
    return;
  }
  formModal.open = false;
}

async function onDelete(card) {
  const result = await store.deleteCard(card.id);
  if (!result.success) {
    notify.error({ title: 'No se pudo eliminar la tarjeta' });
  }
}
</script>
