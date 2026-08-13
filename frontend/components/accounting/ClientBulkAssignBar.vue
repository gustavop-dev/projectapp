<template>
  <!--
    Sticky: the incomes grouped view renders the WHOLE filtered set with no
    pagination, so a selection made at the bottom of a long list used to leave
    the bar off screen. `pr-20` keeps the actions clear of the fixed refresh
    FAB (bottom-6 right-6), which paints above this bar.
  -->
  <div
    v-if="selected.length > 0"
    class="sticky bottom-4 z-20 flex flex-col gap-3 mt-4 p-3 pr-20 rounded-xl border border-border-default bg-surface-raised shadow-lg"
    :data-testid="`${testidPrefix}-bulk-bar`"
  >
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <span class="text-sm text-text-default">
        <span class="whitespace-nowrap">
          <span class="font-semibold tabular-nums">{{ selected.length }}</span>
          seleccionado{{ selected.length === 1 ? '' : 's' }}
        </span>
        <!--
          Selecting survives a filter change, and the action runs on the whole
          selection — so when part of it no longer passes the filter, the bar
          says so instead of letting the count disagree with the table.
        -->
        <span
          v-if="outsideCount > 0"
          class="text-xs text-text-muted whitespace-nowrap"
          title="Se marcaron con otro filtro activo. La acción los incluye igual; la confirmación los lista uno por uno."
          :data-testid="`${testidPrefix}-bulk-outside`"
        >
          · {{ outsideCount }} fuera del filtro actual
        </span>
      </span>
      <BaseButton
        v-if="!allFilteredSelected"
        variant="ghost"
        size="sm"
        :data-testid="`${testidPrefix}-select-all-filtered`"
        @click="selectAllFiltered"
      >
        Seleccionar los {{ filteredIds.length }} filtrados
      </BaseButton>
      <!--
        Sin el hint propio del picker: crecía DENTRO de esta celda del flex y,
        con `sm:items-center`, re-centraba toda la fila contra la celda más
        alta — el input subía y los botones quedaban desalineados. La barra lo
        dice abajo, en su línea de estado, donde no mueve nada.
      -->
      <div class="flex-1 min-w-[16rem]">
        <ClientAutocomplete
          v-model="clientId"
          :test-id="`${testidPrefix}-bulk-client`"
          placeholder="Buscar el cliente a asignar..."
          :show-linked-hint="false"
          @select="onClientSelect"
        />
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <BaseButton variant="secondary" size="sm" @click="clearSelection">
          Cancelar
        </BaseButton>
        <!--
          Desvincular es su propio botón, no el mismo con el selector vacío:
          sólo aparece cuando hay algo que desvincular, así que su presencia
          ya dice que la selección tiene cliente.
        -->
        <BaseButton
          v-if="canUnlink"
          variant="danger"
          size="sm"
          :disabled="busy"
          :data-testid="`${testidPrefix}-bulk-unlink`"
          @click="confirmAndSubmit(unlinkPlan)"
        >
          Desvincular cliente
        </BaseButton>
        <BaseButton
          variant="primary"
          size="sm"
          :disabled="Boolean(assignBlockedReason) || busy"
          :data-testid="`${testidPrefix}-bulk-assign`"
          @click="confirmAndSubmit(assignPlan)"
        >
          Asignar cliente
        </BaseButton>
      </div>
    </div>

    <!--
      Una sola línea, nunca vacía: o dice por qué Asignar está apagado, o
      confirma a quién se va a enlazar. La razón va inline y siempre visible,
      no en un tooltip: un botón apagado sin explicación es el mismo callejón
      que el placeholder que escondía el "vacío = desvincular". Y que la línea
      no pueda faltar es lo que mantiene fijo el alto de la barra.

      `truncate` no es cosmético: un nombre largo partido en dos renglones
      volvería a mover la barra. El texto completo queda en el title.
    -->
    <p
      class="flex items-center gap-1.5 text-xs text-text-muted min-w-0"
      :data-testid="`${testidPrefix}-bulk-hint`"
      :title="statusLine.text"
    >
      <component :is="statusLine.icon" class="w-4 h-4 flex-shrink-0" />
      <span class="truncate">{{ statusLine.text }}</span>
    </p>
  </div>

  <ConfirmModal
    v-model="confirmState.open"
    size="lg"
    :title="confirmState.title"
    :message="confirmState.message"
    :confirm-text="confirmState.confirmText"
    :cancel-text="confirmState.cancelText"
    :variant="confirmState.variant"
    @confirm="handleConfirmed"
    @cancel="handleCancelled"
  >
    <ClientBulkAssignSummary
      v-if="pendingPlan"
      :plan="pendingPlan"
      :record-label="recordLabel"
    />
  </ConfirmModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { InformationCircleIcon, LinkIcon } from '@heroicons/vue/24/outline';

import ConfirmModal from '~/components/ConfirmModal.vue';
import ClientBulkAssignSummary from '~/components/accounting/ClientBulkAssignSummary.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { buildAssignmentPlan, describeAssignmentPlan } from '~/utils/clientAssignment';

/**
 * Bulk client (un)assignment bar for the accounting tables that carry a
 * client link — hostings and incomes today, whatever comes next tomorrow.
 *
 * Shared on purpose: the two pages used to hold a byte-identical copy of
 * this block, so a fix in one silently left the other behind.
 *
 * The two operations are two buttons. Assigning needs a client and says so
 * inline when it hasn't got one; unlinking only exists while the selection
 * actually has a client to lose. Either way the operator confirms against a
 * breakdown of what changes and a list of every record involved — this is a
 * mass edit, and the scope has to be visible before it runs, not after.
 */
const props = defineProps({
  /**
   * FULL record list from the store, not the filtered rows: the selection
   * survives filter and page changes, so it can hold off-screen ids.
   */
  rows: { type: Array, default: () => [] },
  /** Selected row ids (v-model:selected). */
  selected: { type: Array, default: () => [] },
  /** Ids currently passing the filters, for "seleccionar los N filtrados". */
  filteredIds: { type: Array, default: () => [] },
  /** `{ singular, plural }` noun for the copy ('hosting' / 'hostings'). */
  entity: { type: Object, required: true },
  /** data-testid prefix, kept per page ('hostings' / 'incomes'). */
  testidPrefix: { type: String, required: true },
  /** (row) => the row's identity in the confirmation list. */
  recordLabel: { type: Function, required: true },
  /** Store mutation in flight: blocks both actions. */
  busy: { type: Boolean, default: false },
});

const emit = defineEmits(['update:selected', 'submit']);

const { confirmState, requestConfirm, handleConfirmed, handleCancelled } =
  useConfirmModal();

const clientId = ref(null);
const clientLabel = ref('');
const pendingPlan = ref(null);

const allFilteredSelected = computed(
  () => props.filteredIds.length > 0
    && props.filteredIds.every((id) => props.selected.includes(id)),
);

/** Selected rows the active filters no longer show — the action still runs on them. */
const outsideCount = computed(() => {
  const filtered = new Set(props.filteredIds);
  return props.selected.filter((id) => !filtered.has(id)).length;
});

const assignPlan = computed(() => buildAssignmentPlan({
  rows: props.rows,
  selectedIds: props.selected,
  mode: 'assign',
  targetClientId: clientId.value,
  targetClientLabel: clientLabel.value,
}));

const unlinkPlan = computed(() => buildAssignmentPlan({
  rows: props.rows,
  selectedIds: props.selected,
  mode: 'unlink',
}));

const canUnlink = computed(() => unlinkPlan.value.toUnlink.length > 0);

/** Empty string = the assign button is live. */
const assignBlockedReason = computed(() => {
  if (!clientId.value) return 'Elige un cliente para poder asignar.';
  if (assignPlan.value.affected.length === 0) {
    return `Todo lo seleccionado ya tiene a ${clientLabel.value}.`;
  }
  return '';
});

/**
 * `assignBlockedReason` sólo queda vacío cuando ya hay cliente Y hay filas que
 * cambiar, así que el else de este ternario es exactamente el caso en que
 * corresponde confirmar el enlace. Por eso la línea nunca está vacía, y por eso
 * la barra no cambia de alto entre estados.
 */
const statusLine = computed(() => {
  if (assignBlockedReason.value) {
    return { text: assignBlockedReason.value, icon: InformationCircleIcon };
  }
  return {
    text: `Cliente enlazado: ${clientLabel.value} (#${clientId.value})`,
    icon: LinkIcon,
  };
});

function selectAllFiltered() {
  emit('update:selected', [...props.filteredIds]);
}

function clearSelection() {
  emit('update:selected', []);
}

function onClientSelect(client) {
  clientLabel.value = client?.name || '';
}

// Typing in the picker drops the committed id without re-emitting `select`,
// so the label has to follow the id or the confirmation would name a client
// that is no longer chosen.
watch(clientId, (id) => {
  if (id == null) clientLabel.value = '';
});

// The page clears the selection after a successful run; the picker resets
// with it so the next batch starts from scratch.
watch(() => props.selected.length, (count) => {
  if (count === 0) {
    clientId.value = null;
    clientLabel.value = '';
  }
});

/**
 * Show the plan, and on confirmation hand the parent only the rows that
 * actually change — the same ones the modal listed, so the count reported
 * afterwards matches what was promised.
 */
async function confirmAndSubmit(plan) {
  if (plan.affected.length === 0) return;
  // Kept after the await on purpose: clearing it here would blank the body
  // while the dialog is still transitioning out.
  pendingPlan.value = plan;
  const copy = describeAssignmentPlan(plan, { entity: props.entity });
  const confirmed = await requestConfirm({ ...copy, cancelText: 'Cancelar' });
  if (!confirmed) return;
  emit('submit', {
    ids: plan.affected.map((row) => row.id),
    client: plan.mode === 'unlink' ? null : plan.targetClientId,
    mode: plan.mode,
    plan,
  });
}
</script>
