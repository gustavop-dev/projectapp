<template>
  <div>
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
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <h1 class="text-2xl font-light text-text-default">Paquetes de horas</h1>
      <BaseButton
        v-if="activeSection === 'catalog'"
        as="NuxtLink"
        variant="primary"
        size="md"
        :to="localePath({ path: '/panel/hour-packages/create', query: { nationality: selectedNationality } })"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nuevo paquete
      </BaseButton>
    </div>

    <div class="mb-6">
      <BaseSegmented v-model="activeSection" :options="sectionOptions" />
    </div>

    <!-- ══════════════ Catálogo ══════════════ -->
    <template v-if="activeSection === 'catalog'">
      <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
        <div>
          <!-- Nationality tabs: prices switch per country -->
          <BaseSegmented v-model="selectedNationality" :options="nationalityOptions" />
          <p class="text-xs text-text-subtle mt-2">
            Los paquetes {{ nationalityLabel }} se cotizan en {{ currentCurrency }}.
          </p>
        </div>
        <BaseSegmented v-model="viewMode" :options="viewModeOptions" />
      </div>

      <!-- Loading -->
      <div v-if="hourPackagesStore.isLoading" class="flex justify-center py-12">
        <div class="w-6 h-6 border-2 border-focus-ring/30 border-t-focus-ring rounded-full animate-spin" />
      </div>

      <div v-else>
        <div v-if="packages.length === 0" class="bg-surface rounded-xl shadow-sm border border-border-muted px-6 py-12 text-center text-text-subtle text-sm">
          Sin paquetes para esta nacionalidad — las propuestas nuevas usarán los paquetes por defecto.
        </div>

        <!-- Cards mode -->
        <HourPackagesCards
          v-else-if="viewMode === 'cards'"
          :packages="packages"
          @delete="handleDelete"
        />

        <!-- Compare mode -->
        <HourPackagesCompare
          v-else-if="viewMode === 'compare'"
          :packages="packages"
          @delete="handleDelete"
        />

        <template v-else>
          <!-- Table mode: mobile cards -->
          <div class="sm:hidden space-y-3">
            <div v-for="pkg in pagedPackages" :key="pkg.id" class="bg-surface rounded-xl shadow-sm border border-border-muted p-4">
              <div class="flex items-start justify-between gap-3 mb-2">
                <NuxtLink :to="localePath(`/panel/hour-packages/${pkg.id}/edit`)" class="text-sm font-medium text-text-default hover:text-text-brand transition-colors leading-tight">
                  {{ pkg.name_es }}
                </NuxtLink>
                <span class="text-[10px] px-2 py-0.5 rounded-full font-medium flex-shrink-0" :class="statusBadgeClass(pkg)">
                  {{ pkg.is_active ? 'Activo' : 'Inactivo' }}
                </span>
              </div>
              <p class="text-xs text-text-subtle mb-1">{{ pkg.hours }} h · {{ formatMoney(pkg.hourly_rate, pkg.currency) }}/h<span v-if="Number(pkg.discount_percent) > 0"> · -{{ pkg.discount_percent }}%</span></p>
              <p class="text-xs text-text-muted mb-3">Efectiva: {{ formatMoney(effectiveRate(pkg), pkg.currency) }}/h · Total: {{ formatMoney(totalPrice(pkg), pkg.currency) }}</p>
              <div class="flex items-center gap-3">
                <NuxtLink :to="localePath(`/panel/hour-packages/${pkg.id}/edit`)" class="text-xs text-text-brand font-medium">Editar</NuxtLink>
                <button class="text-xs text-danger-strong/70 hover:text-danger-strong transition-colors" @click="handleDelete(pkg)">Eliminar</button>
              </div>
            </div>
          </div>

          <!-- Table mode: desktop table -->
          <div class="hidden sm:block bg-surface rounded-xl shadow-sm border border-border-muted overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="border-b border-border-muted text-left">
                    <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Paquete</th>
                    <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Horas</th>
                    <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Tarifa/h</th>
                    <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Desc.</th>
                    <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Tarifa efectiva</th>
                    <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Total</th>
                    <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider">Estado</th>
                    <th class="px-6 py-3 text-xs font-medium text-text-muted uppercase tracking-wider text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-border-muted">
                  <tr v-for="pkg in pagedPackages" :key="pkg.id" class="hover:bg-surface-raised transition-colors">
                    <td class="px-6 py-4">
                      <NuxtLink :to="localePath(`/panel/hour-packages/${pkg.id}/edit`)" class="text-sm font-medium text-text-default hover:text-text-brand transition-colors">
                        {{ pkg.name_es }}
                      </NuxtLink>
                      <p class="text-xs text-text-subtle mt-0.5">{{ pkg.name_en }} · Orden {{ pkg.order }}</p>
                    </td>
                    <td class="px-6 py-4 text-sm text-text-muted">{{ pkg.hours }} h</td>
                    <td class="px-6 py-4 text-sm text-text-muted">{{ formatMoney(pkg.hourly_rate, pkg.currency) }}</td>
                    <td class="px-6 py-4 text-sm text-text-muted">
                      <span v-if="Number(pkg.discount_percent) > 0" class="text-xs px-2 py-0.5 rounded-full font-medium bg-primary-soft text-text-brand">-{{ pkg.discount_percent }}%</span>
                      <span v-else>—</span>
                    </td>
                    <td class="px-6 py-4 text-sm text-text-muted">{{ formatMoney(effectiveRate(pkg), pkg.currency) }}</td>
                    <td class="px-6 py-4 text-sm font-medium text-text-default">{{ formatMoney(totalPrice(pkg), pkg.currency) }}</td>
                    <td class="px-6 py-4">
                      <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusBadgeClass(pkg)">
                        {{ pkg.is_active ? 'Activo' : 'Inactivo' }}
                      </span>
                    </td>
                    <td class="px-6 py-4 text-right">
                      <div class="flex items-center justify-end gap-2">
                        <NuxtLink :to="localePath(`/panel/hour-packages/${pkg.id}/edit`)" class="text-xs text-text-muted hover:text-text-brand dark:hover:text-white transition-colors">Editar</NuxtLink>
                        <button class="text-xs text-danger-strong/70 hover:text-danger-strong transition-colors" @click="handleDelete(pkg)">Eliminar</button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <BasePagination
            v-if="packages.length > 0"
            :current-page="packagesPage"
            :total-pages="packagesTotalPages"
            :total-items="packagesTotalItems"
            :range-from="packagesRangeFrom"
            :range-to="packagesRangeTo"
            class="mt-4"
            @prev="packagesPrev"
            @next="packagesNext"
            @go="packagesGoTo"
          />
        </template>
      </div>
    </template>

    <!-- ══════════════ Configuración ══════════════ -->
    <template v-else>
      <div class="space-y-6 max-w-2xl">
        <section class="bg-surface rounded-xl shadow-sm border border-border-muted p-6">
          <h2 class="text-sm font-medium text-text-default mb-1">Vista por defecto</h2>
          <p class="text-xs text-text-subtle mb-4">
            Modo con el que abre el catálogo al entrar a esta página.
          </p>
          <BaseSegmented
            :model-value="defaultViewMode"
            :options="viewModeOptions"
            data-testid="hour-packages-default-view"
            @update:model-value="saveDefaultViewMode"
          />
        </section>

        <section class="bg-surface rounded-xl shadow-sm border border-border-muted p-6">
          <h2 class="text-sm font-medium text-text-default mb-1">Restablecer paquetes por defecto</h2>
          <p class="text-xs text-text-subtle mb-4">
            Reemplaza el catálogo del país elegido con la escalera por defecto:
            1&nbsp;h, 10&nbsp;h (-5%), 20&nbsp;h (-10%), 60&nbsp;h (-20%) y 180&nbsp;h (-30%)
            sobre la tarifa base (COL $40.000&nbsp;COP/h · MEX $20&nbsp;USD/h · USA $35&nbsp;USD/h).
            Los paquetes actuales de ese país se eliminan.
          </p>
          <div class="flex flex-col sm:flex-row sm:items-center gap-3">
            <BaseSegmented v-model="restoreNationality" :options="nationalityOptions" />
            <BaseButton
              variant="danger"
              size="sm"
              :disabled="hourPackagesStore.isUpdating"
              data-testid="hour-packages-restore-defaults"
              @click="confirmRestore"
            >
              Restablecer
            </BaseButton>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useHourPackagesStore } from '~/stores/hour_packages';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { usePanelNotify } from '~/composables/usePanelNotify';
import BasePagination from '~/components/base/BasePagination.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import HourPackagesCards from '~/components/hour-packages/PackagesCards.vue';
import HourPackagesCompare from '~/components/hour-packages/PackagesCompare.vue';
import { usePagination } from '~/composables/usePagination';
import { effectiveRate, totalPrice, formatPackageMoney as formatMoney } from '~/utils/hourPackagePricing';

const localePath = useLocalePath();

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const CURRENCY_BY_NATIONALITY = { COL: 'COP', MEX: 'USD', USA: 'USD' };

const nationalityOptions = [
  { value: 'COL', label: 'Colombia (COP)', testId: 'hour-packages-tab-col' },
  { value: 'MEX', label: 'México (USD)', testId: 'hour-packages-tab-mex' },
  { value: 'USA', label: 'USA (USD)', testId: 'hour-packages-tab-usa' },
];

const sectionOptions = [
  { value: 'catalog', label: 'Catálogo', testId: 'hour-packages-section-catalog' },
  { value: 'config', label: 'Configuración', testId: 'hour-packages-section-config' },
];

const viewModeOptions = [
  { value: 'table', label: 'Tabla', testId: 'hour-packages-view-table' },
  { value: 'cards', label: 'Tarjetas', testId: 'hour-packages-view-cards' },
  { value: 'compare', label: 'Comparativa', testId: 'hour-packages-view-compare' },
];

const hourPackagesStore = useHourPackagesStore();
const notify = usePanelNotify();
const packages = computed(() => hourPackagesStore.packages);
const selectedNationality = ref('COL');
const activeSection = ref('catalog');
const viewMode = ref('table');
const restoreNationality = ref('COL');
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const defaultViewMode = computed(() => hourPackagesStore.settings?.default_view_mode ?? 'table');

const nationalityLabel = computed(() =>
  ({ COL: 'de Colombia', MEX: 'de México', USA: 'de Estados Unidos' }[selectedNationality.value]));
const currentCurrency = computed(() => CURRENCY_BY_NATIONALITY[selectedNationality.value]);

const {
  currentPage: packagesPage,
  totalPages: packagesTotalPages,
  totalItems: packagesTotalItems,
  rangeFrom: packagesRangeFrom,
  rangeTo: packagesRangeTo,
  paginatedItems: pagedPackages,
  goTo: packagesGoTo,
  next: packagesNext,
  prev: packagesPrev,
} = usePagination(packages, { pageSize: 10 });

onMounted(async () => {
  hourPackagesStore.fetchAdminPackages(selectedNationality.value);
  const result = await hourPackagesStore.fetchSettings();
  if (result.success) viewMode.value = result.data.default_view_mode;
});
watch(selectedNationality, (nationality) => {
  hourPackagesStore.fetchAdminPackages(nationality);
});
usePanelRefresh(() => hourPackagesStore.fetchAdminPackages(selectedNationality.value));

function statusBadgeClass(pkg) {
  return pkg.is_active
    ? 'bg-primary-soft text-text-brand'
    : 'bg-surface-raised text-text-muted';
}

async function saveDefaultViewMode(mode) {
  const result = await hourPackagesStore.updateSettings({ default_view_mode: mode });
  if (result.success) {
    notify.success('Vista por defecto guardada.');
  } else {
    notify.error('No se pudo guardar la vista por defecto.');
  }
}

function confirmRestore() {
  const label = { COL: 'Colombia', MEX: 'México', USA: 'Estados Unidos' }[restoreNationality.value];
  requestConfirm({
    title: 'Restablecer paquetes',
    message: `¿Reemplazar el catálogo de ${label} con los paquetes por defecto? Los paquetes actuales de ese país se eliminan.`,
    variant: 'danger',
    confirmText: 'Restablecer',
    onConfirm: async () => {
      const result = await hourPackagesStore.restoreDefaults(restoreNationality.value);
      if (!result.success) {
        notify.error('No se pudo restablecer el catálogo.');
        return;
      }
      notify.success(`Catálogo de ${label} restablecido.`);
      if (restoreNationality.value === selectedNationality.value) {
        await hourPackagesStore.fetchAdminPackages(selectedNationality.value);
      }
    },
  });
}

function handleDelete(pkg) {
  requestConfirm({
    title: 'Eliminar paquete',
    message: `¿Eliminar "${pkg.name_es}"? Las propuestas ya creadas no se modifican.`,
    variant: 'danger',
    confirmText: 'Eliminar',
    onConfirm: async () => {
      const result = await hourPackagesStore.deletePackage(pkg.id);
      if (result.success) {
        notify.success('Paquete eliminado.');
      } else {
        notify.error('No se pudo eliminar el paquete.');
      }
    },
  });
}
</script>
