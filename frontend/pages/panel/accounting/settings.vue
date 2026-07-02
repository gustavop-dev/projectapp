<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-light text-text-default">Contabilidad — Configuración</h1>
      <p class="text-sm text-text-subtle mt-1">
        Preferencias de notificaciones del módulo contable.
      </p>
    </div>

    <AccountingSubnav active="settings" />

    <!-- Loading -->
    <div v-if="store.isLoading && !store.settings" class="text-center py-16 text-text-subtle text-sm">
      Cargando configuración...
    </div>

    <div v-else class="max-w-2xl">
      <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6">
        <h2 class="text-lg font-bold text-text-default mb-1">Notificaciones por correo</h2>
        <p class="text-sm text-text-muted mb-5">
          Cada creación, edición o eliminación en el módulo contable enviará un correo a estos
          destinatarios.
        </p>

        <!-- Toggle -->
        <div class="flex items-center justify-between gap-3 mb-5">
          <span class="text-sm font-medium text-text-default">Notificaciones activas</span>
          <BaseToggle
            v-model="notificationsEnabled"
            aria-label="Notificaciones activas"
            data-testid="settings-notifications-toggle"
          />
        </div>

        <!-- Recipients -->
        <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">
          Destinatarios
        </p>
        <p v-if="recipients.length === 0" class="text-sm text-text-subtle mb-3">
          Sin destinatarios configurados.
        </p>
        <div v-else class="space-y-2 mb-3">
          <div
            v-for="(row, index) in recipients"
            :key="row.id"
            class="flex items-center gap-2"
          >
            <BaseInput
              v-model="row.value"
              type="email"
              placeholder="correo@dominio.com"
              class="flex-1"
              :data-testid="`settings-recipient-input-${index}`"
            />
            <button
              type="button"
              :aria-label="`Quitar correo ${index + 1}`"
              :data-testid="`settings-recipient-remove-${index}`"
              class="p-2 rounded-lg text-text-subtle hover:text-danger-strong hover:bg-danger-soft transition-colors"
              @click="removeRecipient(index)"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
          </div>
        </div>

        <BaseButton
          variant="secondary"
          size="sm"
          data-testid="settings-add-recipient"
          @click="addRecipient"
        >
          <PlusIcon class="w-4 h-4" />
          <span>Agregar correo</span>
        </BaseButton>

        <div class="flex items-center justify-end pt-5 mt-5 border-t border-border-muted">
          <BaseButton
            variant="primary"
            size="md"
            :disabled="store.isUpdating"
            data-testid="settings-save-button"
            @click="save"
          >
            {{ store.isUpdating ? 'Guardando...' : 'Guardar cambios' }}
          </BaseButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { PlusIcon, TrashIcon } from '@heroicons/vue/24/outline';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingStore } from '~/stores/accounting';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const store = useAccountingStore();
const notify = usePanelNotify();

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const notificationsEnabled = ref(true);
const recipients = ref([]);
let rowId = 0;

function syncFromSettings(settings) {
  notificationsEnabled.value = Boolean(settings?.notifications_enabled);
  recipients.value = (settings?.notification_recipients || []).map((email) => ({
    id: ++rowId,
    value: email,
  }));
}

async function loadSettings() {
  const result = await store.fetchSettings();
  if (result.success) {
    syncFromSettings(result.data);
  } else {
    notify.error({ title: 'No se pudo cargar la configuración', detail: result.message });
  }
}

function addRecipient() {
  recipients.value.push({ id: ++rowId, value: '' });
}

function removeRecipient(index) {
  recipients.value.splice(index, 1);
}

async function save() {
  const nonEmpty = recipients.value
    .map((row) => row.value.trim())
    .filter((value) => value !== '');

  const invalid = nonEmpty.find((value) => !EMAIL_RE.test(value));
  if (invalid) {
    notify.error({
      title: 'Correo inválido',
      detail: `"${invalid}" no parece un correo válido. Corrígelo o elimínalo antes de guardar.`,
    });
    return;
  }

  const result = await store.updateSettings({
    notification_recipients: nonEmpty,
    notifications_enabled: notificationsEnabled.value,
  });
  if (result.success) {
    syncFromSettings(result.data);
    notify.success('Configuración guardada');
  } else {
    notify.error({ title: 'No se pudo guardar la configuración', detail: result.message });
  }
}

onMounted(loadSettings);
usePanelRefresh(loadSettings);
</script>
