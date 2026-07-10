<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-light text-text-default">Configuración</h1>
      <p class="text-sm text-text-subtle mt-1">
        Preferencias de notificaciones del módulo contable.
      </p>
    </div>

    <AccountingSubnav active="settings" />

    <!-- Error -->
    <AccountingErrorState
      v-if="store.error === 'settings_failed' && !store.settings"
      title="No se pudo cargar la configuración"
      :retrying="store.isLoading"
      @retry="loadSettings"
    />

    <!-- Loading -->
    <div v-else-if="store.isLoading && !store.settings" class="text-center py-16 text-text-subtle text-sm">
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

      <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6 mt-4">
        <h2 class="text-lg font-bold text-text-default mb-1">Recordatorio de deuda de tarjetas</h2>
        <p class="text-sm text-text-muted mb-5">
          Cada viernes a las 9:00 a.m. se envía un correo a los destinatarios
          de arriba pidiendo registrar la actualización semanal de la deuda de
          tarjetas; se repite cada 2 días hasta que quede registrada en
          <NuxtLink :to="localePath('/panel/accounting/cards')" class="text-text-brand hover:underline">Tarjetas</NuxtLink>.
        </p>
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-medium text-text-default">Recordatorio activo</span>
          <BaseToggle
            v-model="cardReminderEnabled"
            aria-label="Recordatorio de deuda de tarjetas activo"
            data-testid="settings-card-reminder-toggle"
          />
        </div>
        <p v-if="!notificationsEnabled" class="text-xs text-warning-strong mt-3">
          Las notificaciones generales están apagadas: el recordatorio tampoco
          se enviará mientras sigan así.
        </p>
      </div>

      <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6 mt-4">
        <h2 class="text-lg font-bold text-text-default mb-1">Avisos de vencimiento de hostings</h2>
        <p class="text-sm text-text-muted mb-5">
          Se envía un correo a los destinatarios de arriba 15 días antes del
          vencimiento de cada hosting activo, otro a los 7 días, y luego cada
          5 días hasta que se envíe la cuenta de cobro al cliente desde
          <NuxtLink :to="localePath('/panel/accounting/hostings')" class="text-text-brand hover:underline">Hostings</NuxtLink>.
        </p>
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-medium text-text-default">Avisos activos</span>
          <BaseToggle
            v-model="hostingExpiryReminderEnabled"
            aria-label="Avisos de vencimiento de hostings activos"
            data-testid="settings-hosting-expiry-toggle"
          />
        </div>
        <p v-if="!notificationsEnabled" class="text-xs text-warning-strong mt-3">
          Las notificaciones generales están apagadas: estos avisos tampoco se
          enviarán mientras sigan así.
        </p>
      </div>

      <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6 mt-4">
        <h2 class="text-lg font-bold text-text-default mb-1">Tasa de cambio USD</h2>
        <p class="text-sm text-text-muted mb-4">
          Pesos por dólar de referencia, usada para el KPI de costo mensual en
          USD de los pagos recurrentes. Se guarda con "Guardar cambios".
        </p>
        <div class="max-w-xs">
          <BaseCurrencyInput
            v-model="usdExchangeRate"
            :decimals="2"
            placeholder="4.000"
            data-testid="settings-usd-rate-input"
          />
        </div>
      </div>

      <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6 mt-4">
        <h2 class="text-lg font-bold text-text-default mb-1">Pestañas de filtros guardados</h2>
        <p class="text-sm text-text-muted mb-5">
          Restaura las pestañas predefinidas de cada vista del módulo contable.
          Al restablecer una vista se eliminan sus pestañas personalizadas.
        </p>
        <div class="space-y-2">
          <div
            v-for="view in FILTER_VIEWS"
            :key="view.value"
            class="flex items-center justify-between gap-3"
          >
            <span class="text-sm text-text-default">{{ view.label }}</span>
            <BaseButton
              variant="secondary"
              size="sm"
              :disabled="resettingView !== null"
              :data-testid="`settings-reset-tabs-${view.value}`"
              @click="askResetTabs(view)"
            >
              {{ resettingView === view.value ? 'Restableciendo...' : 'Restablecer' }}
            </BaseButton>
          </div>
        </div>
      </div>
    </div>

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
import { computed, onMounted, ref } from 'vue';
import { PlusIcon, TrashIcon } from '@heroicons/vue/24/outline';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseInput from '~/components/base/BaseInput.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useAccountingStore } from '~/stores/accounting';
import { create_request } from '~/stores/services/request_http';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const localePath = useLocalePath();
const store = useAccountingStore();
const notify = usePanelNotify();

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const notificationsEnabled = ref(true);
const cardReminderEnabled = ref(true);
const hostingExpiryReminderEnabled = ref(true);
const recipients = ref([]);
const usdExchangeRate = ref(null);
let rowId = 0;

function syncFromSettings(settings) {
  notificationsEnabled.value = Boolean(settings?.notifications_enabled);
  cardReminderEnabled.value = Boolean(settings?.card_reminder_enabled);
  hostingExpiryReminderEnabled.value = Boolean(
    settings?.hosting_expiry_reminder_enabled,
  );
  usdExchangeRate.value =
    settings?.usd_exchange_rate != null ? Number(settings.usd_exchange_rate) : null;
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

  if (!usdExchangeRate.value || usdExchangeRate.value < 1) {
    notify.error({
      title: 'Tasa USD inválida',
      detail: 'La tasa de cambio debe ser un número mayor o igual a 1.',
    });
    return;
  }

  const result = await store.updateSettings({
    notification_recipients: nonEmpty,
    notifications_enabled: notificationsEnabled.value,
    card_reminder_enabled: cardReminderEnabled.value,
    hosting_expiry_reminder_enabled: hostingExpiryReminderEnabled.value,
    usd_exchange_rate: usdExchangeRate.value,
  });
  if (result.success) {
    syncFromSettings(result.data);
    notify.success('Configuración guardada');
  } else {
    notify.error({ title: 'No se pudo guardar la configuración', detail: result.message });
  }
}

// -------------------------------------------------------------------
// Saved filter tabs reset (per accounting view)
// -------------------------------------------------------------------

const FILTER_VIEWS = [
  { value: 'accounting_income', label: 'Ingresos' },
  { value: 'accounting_expense', label: 'Gastos' },
  { value: 'accounting_hosting', label: 'Hostings' },
  { value: 'accounting_pocket', label: 'Bolsillo' },
  { value: 'accounting_recurring', label: 'Recurrentes' },
  { value: 'accounting_ads', label: 'Ads' },
];

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

onMounted(loadSettings);
usePanelRefresh(loadSettings);
</script>
