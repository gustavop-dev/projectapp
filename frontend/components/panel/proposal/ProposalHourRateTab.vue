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

      <!-- Mode switch: both labels visible so neither position has to be guessed -->
      <div>
        <span class="block text-xs text-text-muted mb-1">Fuente de la tarifa por hora</span>
        <div class="flex items-center gap-2">
          <button
            type="button"
            data-testid="hour-rate-mode-auto"
            class="text-xs transition-colors"
            :class="isAuto ? 'font-semibold text-text-default' : 'text-text-subtle hover:text-text-muted'"
            @click="mode = 'auto'"
          >
            Automático
          </button>
          <BaseToggle
            :model-value="!isAuto"
            size="sm"
            aria-label="Alternar entre tarifa automática y manual"
            @update:model-value="mode = $event ? 'manual' : 'auto'"
          />
          <button
            type="button"
            data-testid="hour-rate-mode-manual"
            class="text-xs transition-colors"
            :class="!isAuto ? 'font-semibold text-text-default' : 'text-text-subtle hover:text-text-muted'"
            @click="mode = 'manual'"
          >
            Manual
          </button>
        </div>
        <p data-testid="hour-rate-mode-hint" class="text-[11px] text-text-subtle mt-1">
          <template v-if="isAuto">
            Los paquetes y la tarifa salen del catálogo de Paquetes por horas y se
            sincronizan solos: si el catálogo cambia, el PDF de esta propuesta cambia con él.
          </template>
          <template v-else>
            Esta propuesta usa sus propios paquetes. Podés editarlos, agregar y quitar
            filas; el catálogo ya no la toca hasta que uses «Restablecer».
          </template>
        </p>
      </div>

      <!-- Print toggle -->
      <div class="flex items-start gap-2">
        <BaseToggle
          :model-value="packagesEnabled"
          size="sm"
          aria-label="Incluir los paquetes por horas en el PDF"
          @update:model-value="packagesEnabled = $event"
        />
        <div>
          <span data-testid="hour-rate-print-label" class="block text-xs text-text-default">
            {{ packagesEnabled
              ? 'Los paquetes por horas se imprimen en el PDF'
              : 'Los paquetes por horas NO se imprimen en el PDF' }}
          </span>
          <span class="block text-[11px] text-text-subtle">
            La cláusula de alcance se sigue imprimiendo en ambos casos.
          </span>
        </div>
      </div>

      <!-- Manual controls -->
      <div
        v-if="!isAuto"
        class="border border-border-default dark:border-white/[0.08] rounded-xl p-3 bg-surface-raised space-y-2"
      >
        <label class="block max-w-xs">
          <span class="block text-xs text-text-muted mb-0.5">Tarifa base por hora</span>
          <BaseCurrencyInput
            v-model="baseRate"
            data-testid="hour-rate-manual-input"
            :decimals="rateDecimals"
            placeholder="30000"
          />
        </label>
        <p class="text-[11px] text-text-subtle">
          Se aplica a los paquetes que no tengan tarifa propia. Moneda:
          {{ currency }} (la define el catálogo).
        </p>
        <button
          v-if="catalogDefaults"
          type="button"
          data-testid="hour-rate-reset-catalog"
          class="px-3 py-1.5 rounded-lg border border-border-default bg-surface text-xs font-medium text-text-default hover:bg-surface-raised transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="isAtCatalogDefaults"
          @click="resetToCatalogDefaults"
        >
          Restablecer a los valores del catálogo
        </button>
        <p v-if="catalogDefaults" class="text-[11px] text-text-subtle">
          Repone los paquetes tal como están hoy en el catálogo. La propuesta
          <span class="font-medium">sigue en manual</span>: no vuelve a seguirlo hasta
          que pases a automático.
        </p>
      </div>

      <div
        v-if="isAuto && !catalogPackages.length"
        data-testid="hour-rate-empty-catalog"
        class="rounded-lg border border-warning-strong/40 bg-warning-soft px-3 py-2 text-xs text-warning-strong"
      >
        El catálogo no tiene paquetes activos para esta nacionalidad. La previsualización
        usa la última foto guardada en la propuesta.
      </div>

      <!-- Live preview / editor -->
      <div :class="packagesEnabled ? '' : 'opacity-50'">
        <span class="block text-xs font-medium text-text-muted uppercase tracking-wider mb-2">
          {{ isAuto ? 'Previsualización' : 'Paquetes de esta propuesta' }}
        </span>
        <ProposalHourPackagesTable
          :packages="displayPackages"
          :editable="!isAuto"
          :currency="currency"
          :base-rate="baseRate"
          :language="proposal?.language || 'es'"
          @update="updatePackage"
          @remove="removePackage"
          @add="addPackage"
        />
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
import BaseToggle from '~/components/base/BaseToggle.vue';
import ProposalHourPackagesTable from '~/components/panel/proposal/ProposalHourPackagesTable.vue';
import { useProposalStore } from '~/stores/proposals';
import { useHourPackagesStore } from '~/stores/hour_packages';
import { usePanelNotify } from '~/composables/usePanelNotify';

const props = defineProps({
  proposal: { type: Object, required: true },
});
const emit = defineEmits(['dirty-state-change']);

const proposalsStore = useProposalStore();
const hourPackagesStore = useHourPackagesStore();
const notify = usePanelNotify();

const mode = ref('auto');
const packagesEnabled = ref(true);
const baseRate = ref(null);
/** Manual mode only: the proposal's own package list, edited in place. */
const packages = ref([]);
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

// Mirror the backend query exactly (active only, ordered by order then hours) —
// that ordering is where a preview most easily drifts from the PDF.
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

function fromCatalog(pkg) {
  return {
    id: pkg.id,
    name: props.proposal?.language === 'en' ? pkg.name_en : pkg.name_es,
    note: (props.proposal?.language === 'en' ? pkg.note_en : pkg.note_es) || '',
    hours: Number(pkg.hours) || 0,
    discountPercent: Number(pkg.discount_percent) || 0,
    hourlyRate: Number(pkg.hourly_rate) || 0,
  };
}

// Auto previews the live catalog, so it shows what the PDF will actually print
// rather than the stored snapshot, which may be stale. Manual shows the
// proposal's own list. With an empty catalog, auto falls back to the snapshot —
// exactly what the PDF does.
const displayPackages = computed(() => {
  if (!isAuto.value) return packages.value;
  if (catalogPackages.value.length) return catalogPackages.value.map(fromCatalog);
  return content.value.packages || [];
});

// --- catalog defaults (the reset action) ----------------------------------

const catalogDefaults = computed(() => {
  if (!catalogPackages.value.length) return null;
  const base = Number(catalogPackages.value[0].hourly_rate) || 0;
  if (base <= 0) return null;
  return { base, packages: catalogPackages.value.map(fromCatalog) };
});

const isAtCatalogDefaults = computed(() => {
  const defaults = catalogDefaults.value;
  if (!defaults) return false;
  return snapshotOf(defaults.base, defaults.packages) === snapshot();
});

function resetToCatalogDefaults() {
  const defaults = catalogDefaults.value;
  if (!defaults) return;
  baseRate.value = defaults.base;
  packages.value = defaults.packages.map((p) => ({ ...p }));
}

// --- manual editing -------------------------------------------------------

function updatePackage(index, field, value) {
  const row = packages.value[index];
  if (!row) return;
  packages.value = packages.value.map((pkg, idx) => (
    idx === index ? { ...pkg, [field]: value } : pkg
  ));
}

function removePackage(index) {
  // The PDF section makes no sense with an empty table, so the last row stays.
  if (packages.value.length <= 1) return;
  packages.value = packages.value.filter((_, idx) => idx !== index);
}

function addPackage() {
  packages.value = [...packages.value, {
    name: 'Paquete nuevo',
    note: '',
    hours: 10,
    discountPercent: 0,
    hourlyRate: Number(baseRate.value) || 0,
  }];
}

// --- load / dirty tracking ------------------------------------------------

/**
 * The proposal's own package list, resolving the legacy storage shape.
 *
 * Proposals saved before manual owned its packages carry `manualHourlyRate`
 * and `manualPackageRates` (keyed by catalog id) instead of per-package rates.
 * Folding them in here means those proposals open showing the prices they are
 * actually being quoted at, and drop the legacy keys on the next save.
 */
function packagesFromContent(json) {
  const legacyRates = {};
  for (const entry of json.manualPackageRates || []) {
    if (entry?.packageId == null) continue;
    const rate = Number(entry.hourlyRate);
    if (rate > 0) legacyRates[String(entry.packageId)] = rate;
  }
  const legacyBase = Number(json.manualHourlyRate) || 0;
  return (json.packages || []).map((pkg) => {
    const own = Number(pkg.hourlyRate) || 0;
    const legacy = legacyRates[String(pkg.id)] || legacyBase;
    return {
      ...(pkg.id == null ? {} : { id: pkg.id }),
      name: pkg.name || '',
      note: pkg.note || '',
      hours: Number(pkg.hours) || 0,
      discountPercent: Number(pkg.discountPercent) || 0,
      hourlyRate: own > 0 ? own : legacy,
    };
  });
}

function loadFromSection() {
  const json = content.value;
  packagesEnabled.value = json.hourPackagesEnabled !== false;
  baseRate.value = Number(json.manualHourlyRate) || Number(json.hourlyRate) || null;
  packages.value = packagesFromContent(json);
  storedManualCurrency.value = json.manualCurrency || '';

  // A nationality change after a manual rate was set would silently reprint a
  // COP amount as USD. Fall back to auto and say so instead.
  const stored = json.manualCurrency;
  currencyMismatch.value = Boolean(
    json.hourPackagesMode === 'manual' && stored && currency.value
    && stored !== currency.value,
  );
  mode.value = currencyMismatch.value
    ? 'auto'
    : (json.hourPackagesMode === 'manual' ? 'manual' : 'auto');
}

const baseline = ref('');

/**
 * Canonical serialization of the editable state. The package list is included
 * field by field: without it the dirty tracker — and the "already at the
 * catalog values" check — would be blind to every inline edit.
 */
function snapshotOf(rate, packageList) {
  const numeric = Number(rate);
  return JSON.stringify({
    mode: mode.value,
    enabled: packagesEnabled.value,
    rate: Number.isFinite(numeric) && rate !== null && rate !== '' ? numeric : null,
    packages: (packageList || []).map((p) => [
      p.name || '', p.note || '', Number(p.hours) || 0,
      Number(p.discountPercent) || 0, Number(p.hourlyRate) || 0,
    ]),
  });
}

function snapshot() {
  return snapshotOf(baseRate.value, packages.value);
}

const isDirty = computed(() => baseline.value !== '' && baseline.value !== snapshot());

watch(isDirty, (value) => emit('dirty-state-change', value));

// Entering manual with nothing stored would leave an empty table, and the
// minimum is one package — seed from the catalog.
watch(mode, (value, previous) => {
  if (value === 'manual' && previous === 'auto') {
    currencyMismatch.value = false;
    if (!packages.value.length && catalogDefaults.value) resetToCatalogDefaults();
    if (!baseRate.value && catalogDefaults.value) baseRate.value = catalogDefaults.value.base;
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
    // Spread the section as it stands in the store right now, so fields this
    // tab does not own (titles, scope clause) survive untouched.
    const next = { ...(current.content_json || {}) };
    next.hourPackagesMode = mode.value;
    next.hourPackagesEnabled = packagesEnabled.value;

    if (mode.value === 'manual') {
      // Manual owns the list outright, so it is written verbatim and the legacy
      // override keys are consolidated away.
      next.packages = packages.value.map((p) => ({
        ...(p.id == null ? {} : { id: p.id }),
        name: p.name || '',
        note: p.note || '',
        hours: Number(p.hours) || 0,
        discountPercent: Number(p.discountPercent) || 0,
        hourlyRate: Number(p.hourlyRate) || 0,
      }));
      const rate = Number(baseRate.value);
      if (rate > 0) next.hourlyRate = rate;
      next.manualCurrency = currency.value;
      delete next.manualHourlyRate;
      delete next.manualPackageRates;
    }
    // In auto the catalog re-seeds at generation time, so packages/hourlyRate
    // are left exactly as stored: that snapshot is what keeps the manual work
    // recoverable when the switch goes back to manual.

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
        ? 'Paquetes guardados. El PDF ya los usa.'
        : 'Tarifa sincronizada con el catálogo.',
    );
  } finally {
    isSaving.value = false;
  }
}
</script>
