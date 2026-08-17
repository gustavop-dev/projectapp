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
      <!-- Qué se asigna: cliente o proyecto. Un solo toggle en la misma
           barra, porque dos barras sticky pelearían por el mismo lugar. -->
      <BaseSegmented
        v-if="projectEnabled"
        v-model="target"
        size="sm"
        :options="[
          { value: 'client', label: 'Cliente' },
          { value: 'project', label: 'Proyecto' },
        ]"
        :data-testid="`${testidPrefix}-bulk-target`"
      />
      <!--
        Sin el hint propio del picker: crecía DENTRO de esta celda del flex y,
        con `sm:items-center`, re-centraba toda la fila contra la celda más
        alta — el input subía y los botones quedaban desalineados. La barra lo
        dice abajo, en su línea de estado, donde no mueve nada.
      -->
      <div class="flex-1 min-w-[16rem]">
        <ClientAutocomplete
          v-if="target === 'client'"
          v-model="clientId"
          :test-id="`${testidPrefix}-bulk-client`"
          placeholder="Buscar el cliente a asignar..."
          :show-linked-hint="false"
          @select="onClientSelect"
        />
        <ProjectCatalogSelect
          v-else
          v-model="projectId"
          :test-id="`${testidPrefix}-bulk-project`"
          placeholder="Buscar el proyecto a asignar..."
          @select="onProjectSelect"
        />
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <BaseButton variant="secondary" size="sm" @click="clearSelection">
          Cancelar
        </BaseButton>
        <!--
          Registrar abono vive fuera del segmented Cliente/Proyecto: no es un
          "target" (no usa el picker — abre su propio modal, que ES la
          confirmación) y meterlo como tercer segmento dejaría vacía la celda
          del picker. Siempre presente cuando la página lo habilita, sólo
          cambia `disabled`, así la fila no refluye entre selecciones.
        -->
        <BaseButton
          v-if="settleEnabled"
          variant="secondary"
          size="sm"
          :disabled="settleEligibleIds.length === 0 || busy"
          :data-testid="`${testidPrefix}-bulk-settle`"
          @click="emitSettle"
        >
          Registrar abono
        </BaseButton>
        <!--
          Desvincular es su propio botón, no el mismo con el selector vacío:
          sólo aparece cuando hay algo que desvincular, así que su presencia
          ya dice que la selección tiene cliente (o proyecto).
        -->
        <template v-if="target === 'client'">
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
        </template>
        <template v-else>
          <BaseButton
            v-if="canUnlinkProject"
            variant="danger"
            size="sm"
            :disabled="busy"
            :data-testid="`${testidPrefix}-bulk-unlink-project`"
            @click="confirmAndSubmitProject(unlinkProjectPlan)"
          >
            Quitar proyecto
          </BaseButton>
          <BaseButton
            variant="primary"
            size="sm"
            :disabled="Boolean(projectBlockedReason) || busy"
            :data-testid="`${testidPrefix}-bulk-assign-project`"
            @click="confirmAndSubmitProject(assignProjectPlan)"
          >
            Asignar proyecto
          </BaseButton>
        </template>
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
      v-if="pendingPlan && pendingPlanKind === 'client'"
      :plan="pendingPlan"
      :record-label="recordLabel"
    />
    <ProjectBulkAssignSummary
      v-else-if="pendingPlan"
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
import ProjectBulkAssignSummary from '~/components/accounting/ProjectBulkAssignSummary.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import ProjectCatalogSelect from '~/components/accounting/ProjectCatalogSelect.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseSegmented from '~/components/base/BaseSegmented.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { isSettleEligible } from '~/utils/settleAllocation';
import { buildAssignmentPlan, describeAssignmentPlan } from '~/utils/clientAssignment';
import {
  buildProjectAssignmentPlan,
  describeProjectAssignmentPlan,
} from '~/utils/projectAssignment';

/**
 * Bulk (un)assignment bar for the accounting tables — client since the
 * beginning, project behind the `projectEnabled` toggle. One bar for both
 * targets on purpose: two sticky bars would stack over the same corner and
 * duplicate the selection chrome whose layout invariants live above.
 *
 * Shared between hostings and incomes: the two pages used to hold a
 * byte-identical copy of this block, so a fix in one silently left the
 * other behind.
 *
 * Each target keeps its two operations as two buttons. Assigning needs a
 * target and says so inline when it hasn't got one; unlinking only exists
 * while the selection actually has something to lose. Either way the
 * operator confirms against a breakdown of what changes and a list of every
 * record involved — this is a mass edit, and the scope has to be visible
 * before it runs, not after.
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
  /** Offer the Proyecto target (pages whose rows carry a project link). */
  projectEnabled: { type: Boolean, default: false },
  /** Offer "Registrar abono" (incomes only: bulk-settle needs expected rows). */
  settleEnabled: { type: Boolean, default: false },
});

const emit = defineEmits([
  'update:selected', 'submit', 'submit-project', 'submit-settle',
]);

const { confirmState, requestConfirm, handleConfirmed, handleCancelled } =
  useConfirmModal();

const target = ref('client');
const clientId = ref(null);
const clientLabel = ref('');
const projectId = ref(null);
const selectedProjectRow = ref(null);
const pendingPlan = ref(null);
const pendingPlanKind = ref('client');

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

const assignProjectPlan = computed(() => buildProjectAssignmentPlan({
  rows: props.rows,
  selectedIds: props.selected,
  mode: 'assign',
  targetProject: selectedProjectRow.value,
}));

const unlinkProjectPlan = computed(() => buildProjectAssignmentPlan({
  rows: props.rows,
  selectedIds: props.selected,
  mode: 'unlink',
}));

const canUnlinkProject = computed(
  () => unlinkProjectPlan.value.toUnlink.length > 0,
);

/** Selected ids that can take an abono: company expected rows with pending. */
const settleEligibleIds = computed(() => {
  if (!props.settleEnabled) return [];
  const byId = new Map(props.rows.map((row) => [row.id, row]));
  return props.selected.filter((id) => isSettleEligible(byId.get(id)));
});

/** Empty string = the abono button is live. */
const settleBlockedReason = computed(() => {
  if (!props.settleEnabled || settleEligibleIds.value.length > 0) return '';
  return 'Para abonar se necesitan esperados con saldo pendiente.';
});

/** Empty string = the assign button is live. */
const assignBlockedReason = computed(() => {
  if (!clientId.value) return 'Elige un cliente para poder asignar.';
  if (assignPlan.value.affected.length === 0) {
    return `Todo lo seleccionado ya tiene a ${clientLabel.value}.`;
  }
  return '';
});

/** Same contract for the project target: empty string = button live. */
const projectBlockedReason = computed(() => {
  if (!projectId.value) return 'Elige un proyecto para poder asignar.';
  const plan = assignProjectPlan.value;
  if (plan.affected.length > 0) return '';
  if (plan.blockedClientMismatch.length > 0) {
    return `La selección pertenece a otro cliente: "${plan.targetProjectLabel}" es de ${plan.targetClientLabel || 'otro cliente'}.`;
  }
  return `Todo lo seleccionado ya tiene "${plan.targetProjectLabel}".`;
});

/**
 * La razón de bloqueo sólo queda vacía cuando ya hay destino Y hay filas que
 * cambiar, así que el else de cada rama es exactamente el caso en que
 * corresponde confirmar el enlace. Por eso la línea nunca está vacía, y por
 * eso la barra no cambia de alto entre estados ni entre targets.
 */
const statusLine = computed(() => {
  // La razón del abono viaja como sufijo `·` de la misma línea única (el
  // precedente es el sufijo de mismatch del target proyecto): una segunda
  // línea rompería el alto fijo de la barra.
  const settleSuffix = settleBlockedReason.value
    ? ` · ${settleBlockedReason.value}`
    : '';
  if (target.value === 'project') {
    if (projectBlockedReason.value) {
      return {
        text: `${projectBlockedReason.value}${settleSuffix}`,
        icon: InformationCircleIcon,
      };
    }
    const blocked = assignProjectPlan.value.blockedClientMismatch.length;
    const suffix = blocked > 0
      ? ` · ${blocked} de otro cliente no se ${blocked === 1 ? 'toca' : 'tocan'}`
      : '';
    return {
      text: `Proyecto enlazado: ${assignProjectPlan.value.targetProjectLabel} (#${projectId.value})${suffix}${settleSuffix}`,
      icon: LinkIcon,
    };
  }
  if (assignBlockedReason.value) {
    return {
      text: `${assignBlockedReason.value}${settleSuffix}`,
      icon: InformationCircleIcon,
    };
  }
  return {
    text: `Cliente enlazado: ${clientLabel.value} (#${clientId.value})${settleSuffix}`,
    icon: LinkIcon,
  };
});

function selectAllFiltered() {
  emit('update:selected', [...props.filteredIds]);
}

/**
 * Sin ConfirmModal propio: el modal de abono lista cada ingreso y los
 * totales antes de escribir nada — es la misma garantía que el plan de los
 * assigns, con la distribución además. Sólo viajan los elegibles; el modal
 * anuncia cuántos seleccionados quedaron fuera.
 */
function emitSettle() {
  if (settleEligibleIds.value.length === 0) return;
  emit('submit-settle', {
    ids: settleEligibleIds.value,
    excludedCount: props.selected.length - settleEligibleIds.value.length,
  });
}

function clearSelection() {
  emit('update:selected', []);
}

function onClientSelect(client) {
  clientLabel.value = client?.name || '';
}

function onProjectSelect(project) {
  selectedProjectRow.value = project || null;
}

// Typing in the picker drops the committed id without re-emitting `select`,
// so the label has to follow the id or the confirmation would name a target
// that is no longer chosen.
watch(clientId, (id) => {
  if (id == null) clientLabel.value = '';
});
watch(projectId, (id) => {
  if (id == null) selectedProjectRow.value = null;
});

// The page clears the selection after a successful run; both pickers reset
// with it so the next batch starts from scratch.
watch(() => props.selected.length, (count) => {
  if (count === 0) {
    clientId.value = null;
    clientLabel.value = '';
    projectId.value = null;
    selectedProjectRow.value = null;
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
  pendingPlanKind.value = 'client';
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

/** Project twin of `confirmAndSubmit`, emitting `submit-project`. */
async function confirmAndSubmitProject(plan) {
  if (plan.affected.length === 0) return;
  pendingPlan.value = plan;
  pendingPlanKind.value = 'project';
  const copy = describeProjectAssignmentPlan(plan, { entity: props.entity });
  const confirmed = await requestConfirm({ ...copy, cancelText: 'Cancelar' });
  if (!confirmed) return;
  emit('submit-project', {
    ids: plan.affected.map((row) => row.id),
    project: plan.mode === 'unlink' ? null : plan.targetProjectId,
    mode: plan.mode,
    plan,
  });
}
</script>
