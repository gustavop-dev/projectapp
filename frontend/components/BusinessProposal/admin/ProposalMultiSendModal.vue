<template>
  <BaseModal
    :model-value="visible"
    size="xl"
    data-testid="proposal-multi-send-modal"
    @update:model-value="(v) => !v && handleClose()"
    @close="handleClose"
  >
    <div class="sticky top-0 z-10 bg-surface border-b border-border-muted px-6 py-4 flex items-start justify-between gap-3 rounded-t-2xl">
      <div>
        <h2 class="text-lg font-semibold text-text-default">
          Enviar varias propuestas como un solo correo
        </h2>
        <p class="text-xs text-text-muted mt-1">
          Selecciona las propuestas que quieres incluir.
          <span v-if="clientName">Llegará a <strong>{{ clientName }}</strong></span>
          <span v-if="clientEmail" class="text-text-subtle"> ({{ clientEmail }})</span>.
        </p>
      </div>
      <button
        type="button"
        class="text-text-subtle hover:text-text-default text-sm px-2"
        aria-label="Cerrar"
        @click="handleClose"
      >
        ✕
      </button>
    </div>

    <div class="px-6 py-4">
      <div v-if="loading" class="py-12 text-center text-text-muted text-sm">
        Cargando propuestas del cliente…
      </div>

      <div v-else-if="loadError" class="py-10 text-center">
        <p class="text-danger-strong text-sm mb-2">
          No se pudieron cargar las propuestas del cliente.
        </p>
        <p class="text-xs text-text-subtle">{{ loadError }}</p>
      </div>

      <div
        v-else-if="!hasAnyProposals"
        class="py-10 text-center"
      >
        <p class="text-text-muted text-sm mb-2">
          Este cliente solo tiene esta propuesta.
        </p>
        <p class="text-xs text-text-subtle">
          Crea otra propuesta para el mismo cliente y regresa para enviarlas juntas.
        </p>
      </div>

      <div v-else class="space-y-5">
        <div
          v-for="group in visibleGroups"
          :key="group.key"
          class="space-y-2"
        >
          <div class="flex items-center gap-2">
            <span :class="['inline-block w-2 h-2 rounded-full', group.dotClass]" />
            <h3 class="text-xs font-semibold uppercase tracking-wide text-text-muted">
              {{ group.label }}
            </h3>
            <span class="text-[10px] text-text-subtle">({{ group.proposals.length }})</span>
          </div>

          <label
            v-for="p in group.proposals"
            :key="p.id"
            :class="[
              'flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors',
              isSelected(p.id)
                ? 'border-primary-strong bg-primary-soft'
                : 'border-border-muted hover:bg-surface-raised',
            ]"
          >
            <input
              type="checkbox"
              :checked="isSelected(p.id)"
              :disabled="p.id === currentId"
              :data-testid="`proposal-multi-send-option-${p.id}`"
              class="mt-1 h-4 w-4 rounded border-input-border text-primary-strong focus:ring-primary-strong"
              @change="toggle(p.id)"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-sm font-medium text-text-default truncate">
                  {{ p.title }}
                </span>
                <span
                  v-if="p.id === currentId"
                  class="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-primary-soft text-text-brand"
                >
                  Esta propuesta
                </span>
                <span
                  v-if="group.key === 'expired'"
                  class="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-800"
                >
                  Se reabrirá
                </span>
              </div>
              <div class="flex items-center gap-3 mt-1 text-xs text-text-muted">
                <span>{{ formatMoney(p.total_investment, p.currency) }}</span>
                <span v-if="p.expires_at">·</span>
                <span v-if="p.expires_at">
                  {{ p.is_expired ? 'Expirada' : `Vence en ${p.days_remaining} día${p.days_remaining === 1 ? '' : 's'}` }}
                </span>
              </div>
            </div>
          </label>
        </div>
      </div>
    </div>

    <div
      v-if="hasAnyProposals"
      class="sticky bottom-0 z-10 bg-surface border-t border-border-muted px-6 py-4 rounded-b-2xl flex items-center justify-between gap-3"
    >
      <p class="text-sm text-text-muted">
        <strong class="text-text-default">{{ selectedCount }}</strong>
        propuesta{{ selectedCount === 1 ? '' : 's' }} seleccionada{{ selectedCount === 1 ? '' : 's' }}
      </p>
      <div class="flex items-center gap-2">
        <BaseButton
          variant="secondary"
          size="md"
          data-testid="proposal-multi-send-cancel"
          @click="handleClose"
        >
          Cancelar
        </BaseButton>
        <BaseButton
          variant="primary"
          size="md"
          :disabled="!canSend || sending"
          :loading="sending"
          data-testid="proposal-multi-send-confirm"
          @click="handleSend"
        >
          {{ sending ? 'Enviando…' : `Enviar ${selectedCount} propuesta${selectedCount === 1 ? '' : 's'}` }}
        </BaseButton>
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useProposalsStore } from '~/stores/proposals';
import { formatMoney as formatMoneyUtil } from '~/utils/formatMoney';

const props = defineProps({
  visible: { type: Boolean, default: false },
  currentProposal: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['close', 'sent']);

const MAX_PROPOSALS_PER_EMAIL = 10;
const ELIGIBLE_STATUSES = ['draft', 'sent', 'viewed', 'negotiating', 'expired'];

const STATUS_GROUPS = [
  { key: 'draft', label: 'Borradores', match: (p) => p.status === 'draft', dotClass: 'bg-gray-400' },
  {
    key: 'in-progress',
    label: 'Enviadas / Vistas / Negociación',
    match: (p) => ['sent', 'viewed', 'negotiating'].includes(p.status),
    dotClass: 'bg-blue-500',
  },
  {
    key: 'expired',
    label: 'Expiradas',
    match: (p) => p.status === 'expired' || p.is_expired,
    dotClass: 'bg-amber-500',
  },
];

const proposalsStore = useProposalsStore();
const loading = ref(false);
const sending = ref(false);
const candidates = ref([]);
const selectedIds = ref(new Set());
const loadError = ref('');

const currentId = computed(() => props.currentProposal?.id || null);
const clientId = computed(() => props.currentProposal?.client?.id || null);
const clientName = computed(() => props.currentProposal?.client_name || '');
const clientEmail = computed(() => props.currentProposal?.client_email || '');

const groupsAll = computed(() => {
  const seen = new Set();
  const out = STATUS_GROUPS.map((group) => {
    const proposals = candidates.value
      .filter((p) => !seen.has(p.id) && group.match(p))
      .map((p) => {
        seen.add(p.id);
        return p;
      });
    return { ...group, proposals };
  });
  return out;
});

const visibleGroups = computed(() =>
  groupsAll.value.filter((g) => g.proposals.length > 0),
);

const hasAnyProposals = computed(() =>
  groupsAll.value.some((g) => g.proposals.length > 0),
);

const selectedCount = computed(() => selectedIds.value.size);
const canSend = computed(
  () => selectedCount.value >= 2 && selectedCount.value <= MAX_PROPOSALS_PER_EMAIL,
);

function isSelected(id) {
  return selectedIds.value.has(id);
}

function toggle(id) {
  if (id === currentId.value) return;
  if (!selectedIds.value.has(id) && selectedIds.value.size >= MAX_PROPOSALS_PER_EMAIL) return;
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selectedIds.value = next;
}

const formatMoney = formatMoneyUtil;

const TERMINAL_STATUSES = new Set(['finished', 'accepted', 'rejected']);

async function loadCandidates() {
  if (!clientId.value) {
    candidates.value = [];
    return;
  }
  loading.value = true;
  loadError.value = '';
  try {
    const result = await proposalsStore.fetchProposalsByClient(clientId.value);
    if (!result?.success) {
      loadError.value = 'Reintenta en unos segundos.';
      candidates.value = [];
      return;
    }
    const all = Array.isArray(result.data) ? result.data : [];
    candidates.value = all.filter(
      (p) =>
        !TERMINAL_STATUSES.has(p.status)
        && (ELIGIBLE_STATUSES.includes(p.status) || p.is_expired),
    );
    const next = new Set();
    if (currentId.value) next.add(currentId.value);
    selectedIds.value = next;
  } finally {
    loading.value = false;
  }
}

async function handleSend() {
  if (!canSend.value || sending.value) return;
  sending.value = true;
  try {
    const ids = Array.from(selectedIds.value);
    const result = await proposalsStore.sendMultiProposal(currentId.value, ids);
    if (result.success) {
      emit('sent', { count: ids.length, delivery: result.email_delivery });
      handleClose();
    } else {
      emit('sent', { error: result.errors });
    }
  } finally {
    sending.value = false;
  }
}

function handleClose() {
  emit('close');
}

watch(
  () => props.visible,
  (open) => {
    if (open) loadCandidates();
  },
);
</script>
