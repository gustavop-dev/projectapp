<template>
  <div :class="PAGE_MAX_WIDTH">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-light text-text-default">Configuración</h1>
      <p class="text-sm text-text-subtle mt-1">
        Preferencias del módulo contable.
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
      <UnsavedChangesNotice
        v-if="hasChanges"
        class="mb-4"
        :title="unsavedTitle"
        :detail="unsavedDetail"
        :can-save="canSaveNow"
        :saving="store.isUpdating"
        testid="accounting-settings-unsaved-notice"
        @save="save"
        @discard="discardChanges"
      />

      <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6">
        <h2 class="text-lg font-bold text-text-default mb-1">Notificaciones por correo</h2>
        <p class="text-sm text-text-muted mb-5">
          Los avisos internos del módulo — cambios contables, deuda de tarjetas, extractos,
          calendario de cobros y pagos y pagos de hosting — salen a los destinatarios activos de
          esta lista, y solo a ellos. Las cuentas de cobro no: esas van al correo del cliente que
          figura en cada una. El interruptor de abajo apaga todos los envíos de una vez sin
          desarmar la lista.
        </p>

        <!-- Master switch -->
        <div class="flex items-center justify-between gap-3 mb-5">
          <span class="text-sm font-medium text-text-default">Notificaciones activas</span>
          <BaseToggle
            v-model="notificationsEnabled"
            aria-label="Notificaciones activas"
            data-testid="settings-notifications-toggle"
          />
        </div>

        <!-- Recipients: own CRUD, saved per row (like the card catalog below),
             so the page's "Guardar cambios" governs only the toggles. -->
        <NotificationRecipients :notifications-enabled="notificationsEnabled" />

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
        <h2 class="text-lg font-bold text-text-default mb-1">Catálogo de tarjetas</h2>
        <p class="text-sm text-text-muted mb-5">
          Tarjetas de crédito disponibles en
          <NuxtLink :to="localePath('/panel/accounting/cards')" class="text-text-brand hover:underline">Tarjetas</NuxtLink>.
          El cupo se usa para calcular la deuda (cupo − disponible) y
          "extractos desde" define desde qué mes se esperan extractos.
          Cambiar el cupo no modifica los registros históricos.
        </p>
        <AccountingCardCatalog />
      </div>

      <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6 mt-4">
        <h2 class="text-lg font-bold text-text-default mb-1">Recordatorio de extractos</h2>
        <p class="text-sm text-text-muted mb-5">
          Si el extracto del mes anterior de una tarjeta activa no está
          procesado o no tiene su PDF adjunto en
          <NuxtLink :to="localePath('/panel/accounting/statements')" class="text-text-brand hover:underline">Extractos</NuxtLink>,
          se envía un correo a los destinatarios de arriba cada 8 días,
          junto con la alerta de deuda de tarjetas.
        </p>
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-medium text-text-default">Recordatorio activo</span>
          <BaseToggle
            v-model="statementReminderEnabled"
            aria-label="Recordatorio de extractos activo"
            data-testid="settings-statement-reminder-toggle"
          />
        </div>
        <p v-if="!notificationsEnabled" class="text-xs text-warning-strong mt-3">
          Las notificaciones generales están apagadas: el recordatorio tampoco
          se enviará mientras sigan así.
        </p>
      </div>

      <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6 mt-4">
        <h2 class="text-lg font-bold text-text-default mb-1">Calendario de cobros y pagos</h2>
        <p class="text-sm text-text-muted mb-5">
          Un solo correo diario a los destinatarios de arriba con lo que está
          por vencer. De cada fecha se avisa 15 días antes, 7 días antes y el
          día mismo.
        </p>
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-medium text-text-default">Calendario activo</span>
          <BaseToggle
            v-model="paymentCalendarEnabled"
            aria-label="Calendario de cobros y pagos activo"
            data-testid="settings-payment-calendar-toggle"
          />
        </div>

        <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mt-5 mb-2">
          Qué incluye
        </p>
        <ul class="space-y-2.5" data-testid="settings-payment-calendar-sources">
          <li>
            <span class="text-sm text-text-default">Ingresos esperados</span>
            <p class="text-xs text-text-subtle">
              Puedes silenciar un ingreso puntual desde su fila en
              <NuxtLink :to="localePath('/panel/accounting/incomes')" class="text-text-brand hover:underline">Ingresos</NuxtLink>.
            </p>
          </li>
          <li>
            <span class="text-sm text-text-default">Próximo cobro de los gastos recurrentes</span>
            <p class="text-xs text-text-subtle">
              Se calcula con la fecha de referencia del cobro de cada
              <NuxtLink :to="localePath('/panel/accounting/recurring')" class="text-text-brand hover:underline">recurrente</NuxtLink>.
            </p>
          </li>
          <li class="flex items-start justify-between gap-3">
            <div>
              <span class="text-sm text-text-default">Vencimiento de hostings</span>
              <p class="text-xs text-text-subtle">
                15 y 7 días antes, luego cada 5 días hasta que se envíe la
                cuenta de cobro al cliente.
              </p>
            </div>
            <BaseToggle
              v-model="hostingExpiryReminderEnabled"
              :disabled="!paymentCalendarEnabled"
              aria-label="Avisos de vencimiento de hostings activos"
              data-testid="settings-hosting-expiry-toggle"
            />
          </li>
        </ul>

        <div class="mt-5 pt-5 border-t border-border-muted">
          <span class="text-sm font-medium text-text-default">Recordatorio de vencidos</span>
          <p class="text-xs text-text-subtle mb-2">
            Cada cuánto se repite el aviso de un ingreso esperado que ya pasó
            su fecha y sigue sin cobrarse, hasta que se registre el pago, se dé
            por perdido o se silencie.
          </p>
          <BaseSegmented
            v-model="overdueReminderFrequency"
            :options="OVERDUE_FREQUENCY_OPTIONS"
            :disabled="!paymentCalendarEnabled"
            size="sm"
            data-testid="settings-overdue-frequency"
          />
        </div>

        <p v-if="!notificationsEnabled" class="text-xs text-warning-strong mt-3">
          Las notificaciones generales están apagadas: este correo tampoco se
          enviará mientras sigan así.
        </p>
        <p v-else-if="!paymentCalendarEnabled" class="text-xs text-warning-strong mt-3">
          El calendario está apagado: se guarda la frecuencia, pero no saldrá
          ningún aviso hasta que lo actives.
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
        <h2 class="text-lg font-bold text-text-default mb-1">Vista de ingresos</h2>
        <p class="text-sm text-text-muted mb-4">
          Cómo abre
          <NuxtLink :to="localePath('/panel/accounting/incomes')" class="text-text-brand hover:underline">Ingresos</NuxtLink>
          en cada visita: agrupada por cliente o la tabla clásica. El
          selector dentro de la página cambia la vista solo durante la
          visita. Se guarda con "Guardar cambios".
        </p>
        <BaseSegmented
          v-model="incomeDefaultViewMode"
          :options="INCOME_VIEW_OPTIONS"
          size="sm"
          aria-label="Vista por defecto de ingresos"
          data-testid="settings-income-view-mode"
        />
      </div>

      <div class="bg-surface border border-border-muted rounded-xl shadow-sm p-5 sm:p-6 mt-4">
        <h2 class="text-lg font-bold text-text-default mb-1">Pestañas de filtros guardados</h2>
        <p class="text-sm text-text-muted mb-5">
          Elige qué pestañas se muestran en cada vista del módulo contable y en
          qué orden. Restablecer devuelve las predefinidas a su estado original
          y conserva las que hayas guardado tú.
        </p>
        <div class="space-y-2">
          <SavedFilterTabsManager
            v-for="view in FILTER_VIEWS"
            :key="view.value"
            :ref="(el) => registerManager(view.value, el)"
            :view="view.value"
            :label="view.label"
            :is-resetting="resettingView === view.value"
            @reset="askResetTabs"
          />
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

    <!-- El del guard, independiente del de restablecer pestañas. -->
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      :require-type-text="confirmState.requireTypeText"
      :hide-cancel="confirmState.hideCancel"
      :secondary-text="confirmState.secondaryText"
      :secondary-variant="confirmState.secondaryVariant"
      :secondary-hint="confirmState.secondaryHint"
      :loading="confirmState.busy"
      @confirm="handleConfirmed"
      @secondary="handleSecondaryAction"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { PAGE_MAX_WIDTH } from '~/utils/tableLayout';
import { computed, onMounted, ref } from 'vue';
import AccountingCardCatalog from '~/components/accounting/AccountingCardCatalog.vue';
import AccountingSubnav from '~/components/accounting/AccountingSubnav.vue';
import AccountingErrorState from '~/components/accounting/AccountingErrorState.vue';
import NotificationRecipients from '~/components/accounting/NotificationRecipients.vue';
import SavedFilterTabsManager from '~/components/accounting/SavedFilterTabsManager.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import BaseToggle from '~/components/base/BaseToggle.vue';
import ConfirmModal from '~/components/ConfirmModal.vue';
import UnsavedChangesNotice from '~/components/panel/UnsavedChangesNotice.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { useUnsavedGuard } from '~/composables/useUnsavedGuard';
import { useAccountingStore } from '~/stores/accounting';
import { create_request } from '~/stores/services/request_http';

definePageMeta({ layout: 'admin', middleware: ['admin-auth', 'superuser-only'] });

const localePath = useLocalePath();
const store = useAccountingStore();
const notify = usePanelNotify();

const notificationsEnabled = ref(true);
const cardReminderEnabled = ref(true);
const statementReminderEnabled = ref(true);
const hostingExpiryReminderEnabled = ref(true);
const paymentCalendarEnabled = ref(true);
const overdueReminderFrequency = ref('biweekly');
const usdExchangeRate = ref(null);
const incomeDefaultViewMode = ref('grouped');

const INCOME_VIEW_OPTIONS = [
  { value: 'grouped', label: 'Agrupado' },
  { value: 'classic', label: 'Clásico' },
];

const OVERDUE_FREQUENCY_OPTIONS = [
  { value: 'weekly', label: 'Semanal' },
  { value: 'biweekly', label: 'Quincenal' },
];

/**
 * Refs sueltos, sin objeto `form`: el snapshot los junta a mano.
 *
 * El <ConfirmModal> que ya existe en esta página usa estado local propio
 * (`resetConfirmOpen`), no useConfirmModal, así que el guard monta el suyo sin
 * pisarlo.
 */
const {
  hasChanges,
  unsavedTitle,
  unsavedDetail,
  canSaveNow,
  commit: commitBaseline,
  guardedReload,
  discardChanges,
  confirmState,
  handleConfirmed,
  handleSecondaryAction,
  handleCancelled,
} = useUnsavedGuard({
  snapshot: () => ({
    notificationsEnabled: notificationsEnabled.value,
    cardReminderEnabled: cardReminderEnabled.value,
    statementReminderEnabled: statementReminderEnabled.value,
    hostingExpiryReminderEnabled: hostingExpiryReminderEnabled.value,
    paymentCalendarEnabled: paymentCalendarEnabled.value,
    overdueReminderFrequency: overdueReminderFrequency.value,
    usdExchangeRate: usdExchangeRate.value,
    incomeDefaultViewMode: incomeDefaultViewMode.value,
  }),
  labels: {
    notificationsEnabled: 'notificaciones',
    cardReminderEnabled: 'recordatorio de tarjetas',
    statementReminderEnabled: 'recordatorio de extractos',
    hostingExpiryReminderEnabled: 'recordatorio de hostings',
    paymentCalendarEnabled: 'calendario de pagos',
    overdueReminderFrequency: 'frecuencia de recordatorios',
    usdExchangeRate: 'tasa USD',
    incomeDefaultViewMode: 'vista por defecto de ingresos',
  },
  save,
  reload: loadSettings,
});

function syncFromSettings(settings) {
  notificationsEnabled.value = Boolean(settings?.notifications_enabled);
  cardReminderEnabled.value = Boolean(settings?.card_reminder_enabled);
  statementReminderEnabled.value = Boolean(settings?.statement_reminder_enabled);
  hostingExpiryReminderEnabled.value = Boolean(
    settings?.hosting_expiry_reminder_enabled,
  );
  paymentCalendarEnabled.value = Boolean(settings?.payment_calendar_enabled);
  // Anything unknown lands on 'biweekly', the backend default.
  overdueReminderFrequency.value =
    settings?.overdue_reminder_frequency === 'weekly' ? 'weekly' : 'biweekly';
  // Anything unknown lands on 'grouped', the backend default.
  incomeDefaultViewMode.value =
    settings?.income_default_view_mode === 'classic' ? 'classic' : 'grouped';
  usdExchangeRate.value =
    settings?.usd_exchange_rate != null ? Number(settings.usd_exchange_rate) : null;
  // Único punto de hidratación: sirve para la carga, el refresh y el eco
  // posterior a guardar.
  commitBaseline();
}

async function loadSettings() {
  const result = await store.fetchSettings();
  if (result.success) {
    syncFromSettings(result.data);
  } else {
    notify.error({ title: 'No se pudo cargar la configuración', detail: result.message });
  }
}

async function save() {
  const payload = {
    notifications_enabled: notificationsEnabled.value,
    card_reminder_enabled: cardReminderEnabled.value,
    statement_reminder_enabled: statementReminderEnabled.value,
    hosting_expiry_reminder_enabled: hostingExpiryReminderEnabled.value,
    payment_calendar_enabled: paymentCalendarEnabled.value,
    overdue_reminder_frequency: overdueReminderFrequency.value,
    income_default_view_mode: incomeDefaultViewMode.value,
  };
  // Only send the rate when the user has one loaded/typed: the backend
  // keeps its current value otherwise.
  if (usdExchangeRate.value != null) {
    if (usdExchangeRate.value < 1) {
      notify.error({
        title: 'Tasa USD inválida',
        detail: 'La tasa de cambio debe ser un número mayor o igual a 1.',
      });
      return false;
    }
    payload.usd_exchange_rate = usdExchangeRate.value;
  }

  const result = await store.updateSettings(payload);
  if (result.success) {
    // syncFromSettings re-fija la baseline con el eco del servidor.
    syncFromSettings(result.data);
    notify.success('Configuración guardada');
    return true;
  }
  notify.error({ title: 'No se pudo guardar la configuración', detail: result.message });
  // Sin re-baseline: un guardado fallido deja el aviso puesto.
  return false;
}

// -------------------------------------------------------------------
// Saved filter tabs reset (per accounting view)
// -------------------------------------------------------------------

// Every accounting view with a filter strip, so the order and visibility of
// all of them are administrable from one place. Cuentas de cobro and Tarjetas
// have no seeded tabs, but they do save their own and carry builtins, and
// leaving them out was what made them the two views whose strip could not be
// reordered, hidden or restored.
const FILTER_VIEWS = [
  { value: 'accounting_income', label: 'Ingresos' },
  { value: 'accounting_expense', label: 'Gastos' },
  { value: 'accounting_hosting', label: 'Hostings' },
  { value: 'accounting_collections', label: 'Cuentas de cobro' },
  { value: 'accounting_pocket', label: 'Bolsillo' },
  { value: 'accounting_recurring', label: 'Recurrentes' },
  { value: 'accounting_cards', label: 'Tarjetas' },
  { value: 'accounting_ads', label: 'Ads' },
  { value: 'accounting_history_sends', label: 'Historial · Envíos' },
  { value: 'accounting_history_changes', label: 'Historial · Cambios' },
];

const resetConfirmOpen = ref(false);
const pendingResetView = ref(null);
const resettingView = ref(null);
const managers = new Map();

function registerManager(view, el) {
  if (el) managers.set(view, el);
  else managers.delete(view);
}

const resetConfirmMessage = computed(() =>
  pendingResetView.value
    ? `Las pestañas predefinidas de "${pendingResetView.value.label}" volverán a ` +
      'su estado original. Las que guardaste tú se conservan.'
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
    await managers.get(view.value)?.refresh();
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
// El refresh vuelve a traer la configuración por encima: que pregunte antes.
usePanelRefresh(guardedReload);
</script>
