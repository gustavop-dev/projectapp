<template>
  <div class="space-y-4">
    <!-- No commercial_conditions section yet (proposals older than the section) -->
    <div
      v-if="!section"
      data-testid="hour-rate-no-section"
      class="border border-border-default dark:border-white/[0.08] rounded-xl p-6 bg-surface-raised text-center"
    >
      <p class="text-sm text-text-muted">
        Esta propuesta todavía no tiene la sección «Condiciones comerciales», que es
        donde viven los paquetes por horas del PDF.
      </p>
      <button
        type="button"
        data-testid="hour-rate-create-section"
        class="mt-3 px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium disabled:opacity-60 disabled:cursor-not-allowed"
        :disabled="isCreating"
        @click="createSection"
      >
        {{ isCreating ? 'Creando…' : 'Crear la sección' }}
      </button>
    </div>

    <template v-else>
      <!-- The tab can happily edit a section that never reaches the PDF -->
      <div
        v-if="section.is_enabled === false"
        data-testid="hour-rate-disabled-warning"
        class="rounded-lg border border-warning-strong/40 bg-warning-soft px-3 py-2 text-xs text-warning-strong"
      >
        La sección «Condiciones comerciales» está deshabilitada, así que estos paquetes
        no se imprimen en el PDF. Habilitala desde la pestaña Secciones.
      </div>

      <!-- The manual rate was typed in a currency this proposal no longer bills in -->
      <div
        v-if="currencyMismatch"
        data-testid="hour-rate-currency-mismatch"
        class="rounded-lg border border-danger-strong/40 bg-danger-soft px-3 py-2 text-xs text-danger-strong"
      >
        La tarifa manual se guardó en {{ storedManualCurrency }} y esta propuesta ahora
        factura en {{ currency }}. Se volvió a modo automático para no imprimir un monto
        equivocado: revisá la tarifa antes de reactivar el modo manual.
      </div>

      <!-- Mode switch -->
      <div>
        <span class="block text-xs text-text-muted mb-1">Fuente de la tarifa por hora</span>
        <BaseSegmented v-model="mode" :options="MODE_OPTIONS" size="sm" />
        <p data-testid="hour-rate-mode-hint" class="text-[11px] text-text-subtle mt-1">
          <template v-if="isAuto">
            La tarifa sale del catálogo de Paquetes por horas y se sincroniza sola: si el
            catálogo cambia, el PDF de esta propuesta cambia con él.
          </template>
          <template v-else>
            Esta propuesta usa su propia tarifa. Los nombres, las horas y los descuentos
            siguen viniendo del catálogo; sólo cambia el precio de la hora, y sólo acá.
          </template>
        </p>
      </div>

      <!-- Manual inputs -->
      <div
        v-if="!isAuto"
        class="border border-border-default dark:border-white/[0.08] rounded-xl p-3 bg-surface-raised space-y-2"
      >
        <label class="block">
          <span class="block text-xs text-text-muted mb-0.5">Tarifa por hora</span>
          <BaseCurrencyInput
            v-model="manualHourlyRate"
            data-testid="hour-rate-manual-input"
            :decimals="rateDecimals"
            placeholder="30000"
          />
        </label>
        <p class="text-[11px] text-text-subtle">
          Es la tarifa <span class="font-medium">antes del descuento</span>: el descuento de
          cada paquete se aplica encima. Moneda: {{ currency }} (la define el catálogo).
        </p>
        <div class="flex flex-wrap items-center gap-x-4 gap-y-1">
          <button
            v-if="hasOverrides"
            type="button"
            data-testid="hour-rate-clear-overrides"
            class="text-xs font-medium text-text-brand hover:underline"
            @click="clearOverrides"
          >
            Aplicar esta tarifa a todos los paquetes
          </button>
          <button
            v-if="catalogDefaults"
            type="button"
            data-testid="hour-rate-reset-catalog"
            class="text-xs font-medium text-text-brand hover:underline disabled:opacity-50 disabled:cursor-not-allowed disabled:no-underline"
            :disabled="isAtCatalogDefaults"
            @click="resetToCatalogDefaults"
          >
            Restablecer a los valores del catálogo
          </button>
        </div>
        <p v-if="catalogDefaults" class="text-[11px] text-text-subtle">
          Restablecer copia las tarifas del catálogo pero la propuesta
          <span class="font-medium">sigue en manual</span>: queda con los valores de hoy y
          no vuelve a seguir al catálogo hasta que pases a automático.
        </p>
      </div>

      <div
        v-if="!catalogPackages.length"
        data-testid="hour-rate-empty-catalog"
        class="rounded-lg border border-warning-strong/40 bg-warning-soft px-3 py-2 text-xs text-warning-strong"
      >
        El catálogo no tiene paquetes activos para esta nacionalidad. La previsualización
        usa la última foto guardada en la propuesta.
      </div>

      <!-- Live preview: the same table the PDF prints -->
      <div>
        <span class="block text-xs font-medium text-text-muted uppercase tracking-wider mb-2">
          Previsualización
        </span>
        <div class="overflow-x-auto">
          <table data-testid="hour-rate-preview" class="w-full text-sm">
            <thead>
              <tr class="border-b border-border-default dark:border-white/[0.08]">
                <th class="text-left font-medium text-text-muted py-2 pr-2">{{ labels.package }}</th>
                <th class="text-center font-medium text-text-muted py-2 px-2">{{ labels.hours }}</th>
                <th class="text-center font-medium text-text-muted py-2 px-2">{{ labels.discount }}</th>
                <th class="text-right font-medium text-text-muted py-2 px-2">{{ labels.rate }}</th>
                <th class="text-right font-medium text-text-muted py-2 pl-2">{{ labels.total }}</th>
                <th v-if="!isAuto" class="text-right font-medium text-text-muted py-2 pl-2">Tarifa propia</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in previewRows"
                :key="row.key"
                :data-testid="`hour-rate-row-${row.key}`"
                class="border-b border-border-default/60 dark:border-white/[0.05]"
              >
                <td class="py-2 pr-2">
                  <span class="font-medium text-text-default">{{ row.name }}</span>
                  <span v-if="row.note" class="block text-[11px] text-text-subtle">{{ row.note }}</span>
                </td>
                <td class="text-center text-text-default py-2 px-2">{{ row.hours }} h</td>
                <td class="text-center text-text-default py-2 px-2">{{ row.discountLabel }}</td>
                <td class="text-right text-text-default py-2 px-2" :data-testid="`hour-rate-rate-${row.key}`">
                  {{ row.rateLabel }}/h
                </td>
                <td class="text-right font-medium text-text-default py-2 pl-2" :data-testid="`hour-rate-total-${row.key}`">
                  {{ row.totalLabel }}
                </td>
                <td v-if="!isAuto" class="py-2 pl-2 w-40">
                  <BaseCurrencyInput
                    v-if="row.id != null"
                    :modelValue="overrideFor(row.id)"
                    :data-testid="`hour-rate-override-${row.id}`"
                    :decimals="rateDecimals"
                    size="sm"
                    placeholder="Usa la tarifa base"
                    @update:modelValue="setOverride(row.id, $event)"
                  />
                  <span v-else class="text-[11px] text-text-subtle">—</span>
                </td>
              </tr>
              <tr v-if="!previewRows.length">
                <td colspan="6" class="py-4 text-center text-xs text-text-subtle">
                  No hay paquetes para mostrar.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button
          type="button"
          data-testid="hour-rate-save"
          class="px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium disabled:opacity-60 disabled:cursor-not-allowed"
          :disabled="!isDirty || isSaving"
          @click="save"
        >
          {{ isSaving ? 'Guardando…' : 'Guardar' }}
        </button>
        <span v-if="isDirty" class="text-xs text-warning-strong">Cambios sin guardar</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import BaseCurrencyInput from '~/components/base/BaseCurrencyInput.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import { useProposalStore } from '~/stores/proposals';
import { useHourPackagesStore } from '~/stores/hour_packages';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { effectiveRate, totalPrice, formatPackageMoney } from '~/utils/hourPackagePricing.js';

const props = defineProps({
  proposal: { type: Object, required: true },
});
const emit = defineEmits(['dirty-state-change']);

const proposalsStore = useProposalStore();
const hourPackagesStore = useHourPackagesStore();
const notify = usePanelNotify();

const MODE_OPTIONS = [
  { value: 'auto', label: 'Automático (catálogo)', testId: 'hour-rate-mode-auto' },
  { value: 'manual', label: 'Manual', testId: 'hour-rate-mode-manual' },
];

const mode = ref('auto');
const manualHourlyRate = ref(null);
const overrides = ref({});
const isSaving = ref(false);
const isCreating = ref(false);
const currencyMismatch = ref(false);
const storedManualCurrency = ref('');

const isAuto = computed(() => mode.value !== 'manual');

// Always resolved from the store rather than cached on mount, so a concurrent
// save from the Secciones tab is not silently overwritten by a stale copy.
const section = computed(() => (proposalsStore.currentProposal?.sections || [])
  .find((s) => s.section_type === 'commercial_conditions') || null);

const content = computed(() => section.value?.content_json || {});

// The catalog is the source of truth for structure in BOTH modes. Mirror the
// backend query exactly (active only, ordered by order then hours) — that
// ordering is where a preview most easily drifts from the PDF.
const catalogPackages = computed(() => (hourPackagesStore.packages || [])
  .filter((p) => p.is_active)
  .slice()
  .sort((a, b) => (a.order - b.order) || (a.hours - b.hours)));

const currency = computed(() => catalogPackages.value[0]?.currency
  || content.value.currency
  || props.proposal?.currency
  || 'COP');

// COP shows whole pesos; USD keeps cents (mirrors BaseCurrencyInput usage).
const rateDecimals = computed(() => (currency.value === 'COP' ? 0 : 2));

const isEnglish = computed(() => props.proposal?.language === 'en');

const labels = computed(() => {
  // Tax label lives inside the header in parentheses, like the PDF.
  const tax = currency.value === 'USD' ? '+ Tax' : '+ IVA';
  return isEnglish.value
    ? { package: 'Package', hours: 'Hours', discount: 'Disc.', rate: `Rate/hour (${tax})`, total: `Total (${tax})` }
    : { package: 'Paquete', hours: 'Horas', discount: 'Dcto.', rate: `Tarifa/hora (${tax})`, total: `Total (${tax})` };
});

// Preview rows come from the live catalog; only when it is empty do we fall
// back to the stored snapshot, which is exactly what the PDF does.
const sourceRows = computed(() => {
  if (catalogPackages.value.length) {
    return catalogPackages.value.map((p) => ({
      id: p.id,
      name: isEnglish.value ? p.name_en : p.name_es,
      note: isEnglish.value ? p.note_en : p.note_es,
      hours: Number(p.hours) || 0,
      discountPercent: Number(p.discount_percent) || 0,
      catalogRate: Number(p.hourly_rate) || 0,
    }));
  }
  return (content.value.packages || []).map((p, idx) => ({
    id: p.id ?? null,
    key: `snapshot-${idx}`,
    name: p.name || '',
    note: p.note || '',
    hours: Number(p.hours) || 0,
    discountPercent: Number(p.discountPercent) || 0,
    catalogRate: Number(p.hourlyRate) || Number(content.value.hourlyRate) || 0,
  }));
});

function resolvedRate(row) {
  if (isAuto.value) return row.catalogRate;
  const own = row.id == null ? null : overrides.value[String(row.id)];
  if (own != null && Number(own) > 0) return Number(own);
  const base = Number(manualHourlyRate.value);
  return base > 0 ? base : row.catalogRate;
}

const previewRows = computed(() => sourceRows.value.map((row, idx) => {
  // hourPackagePricing speaks the catalog's snake_case shape.
  const snake = {
    hourly_rate: resolvedRate(row),
    discount_percent: row.discountPercent,
    hours: row.hours,
  };
  return {
    ...row,
    key: row.key || row.id || `row-${idx}`,
    discountLabel: row.discountPercent ? `-${row.discountPercent}%` : '—',
    rateLabel: formatPackageMoney(effectiveRate(snake), currency.value),
    totalLabel: formatPackageMoney(totalPrice(snake), currency.value),
  };
}));

const hasOverrides = computed(() => Object.keys(overrides.value).length > 0);

function overrideFor(id) {
  const value = overrides.value[String(id)];
  return value == null ? null : value;
}

function setOverride(id, value) {
  const next = { ...overrides.value };
  if (value == null || value === '' || Number(value) <= 0) {
    delete next[String(id)];
  } else {
    next[String(id)] = Number(value);
  }
  overrides.value = next;
}

function clearOverrides() {
  overrides.value = {};
}

// The manual configuration that reproduces automatic mode exactly.
//
// Catalog packages can carry different rates from one another, so this is NOT
// "the base rate with no overrides" — that would flatten every package onto the
// first one's rate and quietly price the proposal differently from auto. It
// mirrors the seeder instead (hour_package_service.seed_commercial_conditions_
// from_catalog): the first package's rate is the baseline, and any package that
// charges something else carries its own override. Packages that match the base
// get no entry, so the table does not fill up with redundant inputs.
const catalogDefaults = computed(() => {
  const packages = catalogPackages.value;
  if (!packages.length) return null;
  const base = Number(packages[0].hourly_rate) || 0;
  if (base <= 0) return null;
  const result = {};
  for (const pkg of packages) {
    const rate = Number(pkg.hourly_rate) || 0;
    if (rate > 0 && rate !== base) result[String(pkg.id)] = rate;
  }
  return { base, overrides: result };
});

// Compared through the same serializer the dirty tracker uses, so "already at
// the defaults" and "no unsaved changes" can never disagree about equality.
const isAtCatalogDefaults = computed(() => {
  const defaults = catalogDefaults.value;
  if (!defaults) return false;
  return snapshot() === snapshotOf(defaults.base, defaults.overrides);
});

function resetToCatalogDefaults() {
  const defaults = catalogDefaults.value;
  if (!defaults) return;
  manualHourlyRate.value = defaults.base;
  overrides.value = { ...defaults.overrides };
}

// --- load / dirty tracking ------------------------------------------------

function overridesFromContent(json) {
  const result = {};
  for (const entry of json.manualPackageRates || []) {
    if (entry?.packageId == null) continue;
    const rate = Number(entry.hourlyRate);
    if (rate > 0) result[String(entry.packageId)] = rate;
  }
  return result;
}

function loadFromSection() {
  const json = content.value;
  manualHourlyRate.value = json.manualHourlyRate ?? null;
  overrides.value = overridesFromContent(json);
  storedManualCurrency.value = json.manualCurrency || '';

  // A nationality change after a manual rate was set would silently reprint a
  // COP amount as USD. Fall back to auto and say so instead.
  const stored = json.manualCurrency;
  const hasManualValue = json.manualHourlyRate != null
    || Object.keys(overrides.value).length > 0;
  currencyMismatch.value = Boolean(
    json.hourPackagesMode === 'manual' && hasManualValue
    && stored && currency.value && stored !== currency.value,
  );
  mode.value = currencyMismatch.value
    ? 'auto'
    : (json.hourPackagesMode === 'manual' ? 'manual' : 'auto');
}

const baseline = ref('');

// Canonical serialization of the editable state. Override keys are sorted and
// the rate is coerced: JSON.stringify preserves insertion order, so two maps
// holding the same rates would otherwise compare as different depending on the
// order they were typed in.
function snapshotOf(rate, overrideMap) {
  const numeric = Number(rate);
  return JSON.stringify({
    mode: mode.value,
    rate: Number.isFinite(numeric) && rate !== null && rate !== '' ? numeric : null,
    overrides: Object.keys(overrideMap || {}).sort().map(
      (id) => [id, Number(overrideMap[id])],
    ),
  });
}

function snapshot() {
  return snapshotOf(manualHourlyRate.value, overrides.value);
}

const isDirty = computed(() => baseline.value !== '' && baseline.value !== snapshot());

watch(isDirty, (value) => emit('dirty-state-change', value));

// Prefill the manual rate from the catalog the first time manual is enabled,
// so the field never starts empty and print a $0 table.
watch(mode, (value, previous) => {
  if (value === 'manual' && previous === 'auto') {
    currencyMismatch.value = false;
    if (manualHourlyRate.value == null || Number(manualHourlyRate.value) <= 0) {
      manualHourlyRate.value = catalogPackages.value[0]?.hourly_rate
        ? Number(catalogPackages.value[0].hourly_rate)
        : null;
    }
  }
});

watch(section, (value, previous) => {
  if (value && value.id !== previous?.id) {
    loadFromSection();
    baseline.value = snapshot();
  }
}, { immediate: true });

watch(() => props.proposal?.nationality, async (nationality) => {
  if (!nationality) return;
  await hourPackagesStore.fetchAdminPackages(nationality);
  loadFromSection();
  baseline.value = snapshot();
}, { immediate: true });

// --- actions --------------------------------------------------------------

async function createSection() {
  isCreating.value = true;
  try {
    const result = await proposalsStore.createSection(props.proposal.id, 'commercial_conditions');
    if (result?.success === false) {
      notify.error('No se pudo crear la sección de condiciones comerciales.');
      return;
    }
    loadFromSection();
    baseline.value = snapshot();
    notify.success('Sección creada.');
  } finally {
    isCreating.value = false;
  }
}

async function save() {
  const current = section.value;
  if (!current) return;
  isSaving.value = true;
  try {
    // Spread the section as it stands in the store right now, and write only
    // the rate keys: packages, currency and hourlyRate stay catalog-owned.
    const next = { ...(current.content_json || {}) };
    next.hourPackagesMode = mode.value;

    // An empty rate is removed rather than stored as 0, which the PDF would
    // print as $0 packages instead of falling back to the catalog.
    const rate = Number(manualHourlyRate.value);
    if (rate > 0) {
      next.manualHourlyRate = rate;
    } else if (mode.value === 'manual') {
      delete next.manualHourlyRate;
    }

    const entries = Object.entries(overrides.value)
      .map(([packageId, hourlyRate]) => ({ packageId: Number(packageId), hourlyRate }));
    if (entries.length) {
      next.manualPackageRates = entries;
    } else {
      delete next.manualPackageRates;
    }

    // Stamp the currency whenever a manual value is stored, so a later change
    // of nationality is detectable instead of silently reprinting COP as USD.
    if (rate > 0 || entries.length) {
      next.manualCurrency = currency.value;
    } else {
      delete next.manualCurrency;
    }

    const result = await proposalsStore.updateSection(current.id, {
      title: current.title,
      is_wide_panel: current.is_wide_panel,
      content_json: next,
    });
    if (result?.success === false) {
      notify.error('No se pudo guardar la tarifa.');
      return;
    }
    baseline.value = snapshot();
    storedManualCurrency.value = next.manualCurrency || '';
    notify.success(
      mode.value === 'manual'
        ? 'Tarifa manual guardada. El PDF ya la usa.'
        : 'Tarifa sincronizada con el catálogo.',
    );
  } finally {
    isSaving.value = false;
  }
}
</script>
