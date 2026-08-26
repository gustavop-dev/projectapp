<template>
  <BaseModal
    :model-value="open"
    kind="form"
    size="lg"
    title-id="bulk-assign-title"
    @close="emit('close')"
  >
    <div
      class="flex h-full min-h-0 flex-col panel-portrait:min-h-[min(36rem,calc(90dvh-2rem))]"
      :data-testid="`${testidPrefix}-bulk-assign-modal`"
    >
      <div class="shrink-0 px-6 pt-6 pb-2">
        <h3 id="bulk-assign-title" class="text-lg font-bold text-text-default">
          {{ isClient ? 'Asignar cliente' : 'Asignar proyecto' }}
        </h3>
        <p class="text-sm text-text-subtle mt-1">
          {{ selectedCount }}
          {{ selectedCount === 1 ? entity.singular : entity.plural }}
          seleccionad{{ selectedCount === 1 ? 'o' : 'os' }}. Elige el destino y
          revisa el alcance antes de confirmar.
        </p>
      </div>

      <!-- El listbox flota fuera del panel: esta zona conserva sitio para el
           alcance y no compite con el desplegable por el scroll del modal. -->
      <div class="min-h-0 flex-1 px-6 py-4 space-y-4">
        <ClientAutocomplete
          v-if="isClient"
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

        <ClientBulkAssignSummary
          v-if="isClient && hasTarget"
          :plan="plan"
          :record-label="recordLabel"
        />
        <ProjectBulkAssignSummary
          v-else-if="hasTarget"
          :plan="plan"
          :record-label="recordLabel"
        />
      </div>

      <!--
        Una sola línea, nunca vacía: o dice por qué Asignar está apagado, o
        confirma a quién se va a enlazar. Es la misma garantía que daba la
        barra antes del menú — un botón apagado sin razón visible es un
        callejón sin salida — sólo que ahora vive pegada al botón que gobierna.
      -->
      <div class="flex shrink-0 items-center justify-between gap-3 px-6 pb-6 pt-2">
        <p
          class="flex items-center gap-1.5 text-xs text-text-muted min-w-0"
          :data-testid="`${testidPrefix}-bulk-hint`"
          :title="statusLine.text"
          aria-live="polite"
        >
          <component :is="statusLine.icon" class="w-4 h-4 flex-shrink-0" />
          <span class="truncate">{{ statusLine.text }}</span>
        </p>
        <div class="flex items-center gap-2 flex-shrink-0">
          <BaseButton
            variant="secondary"
            size="sm"
            :data-testid="`${testidPrefix}-bulk-assign-cancel`"
            @click="emit('close')"
          >
            Cancelar
          </BaseButton>
          <BaseButton
            variant="primary"
            size="sm"
            :disabled="Boolean(blockedReason) || busy"
            :data-testid="isClient
              ? `${testidPrefix}-bulk-assign`
              : `${testidPrefix}-bulk-assign-project`"
            @click="confirm"
          >
            {{ isClient ? 'Asignar cliente' : 'Asignar proyecto' }}
          </BaseButton>
        </div>
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { InformationCircleIcon, LinkIcon } from '@heroicons/vue/24/outline';

import ClientBulkAssignSummary from '~/components/accounting/ClientBulkAssignSummary.vue';
import ProjectBulkAssignSummary from '~/components/accounting/ProjectBulkAssignSummary.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import ProjectCatalogSelect from '~/components/accounting/ProjectCatalogSelect.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseModal from '~/components/base/BaseModal.vue';
import { buildAssignmentPlan } from '~/utils/clientAssignment';
import { buildProjectAssignmentPlan } from '~/utils/projectAssignment';

/**
 * Bulk assignment of a client or a project to the current selection.
 *
 * Lives in a modal rather than inline in the bulk bar because the bar had
 * grown to six controls with two of them belonging to different operations
 * entirely. One component for both targets on purpose: they differ only in
 * picker, plan builder and summary — the chrome around them (the live plan,
 * the never-empty reason line, the gated confirm) is the whole value, and a
 * second copy of it is exactly the drift the shared bar was created to stop.
 *
 * This is a mass edit, so the scope has to be visible BEFORE it runs: the
 * summary lists every affected record, and the confirm stays disabled with
 * the reason on screen until there is actually something to change.
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  /** Which side is being assigned. */
  target: { type: String, default: 'client' },
  /** FULL record list from the store, not the filtered rows. */
  rows: { type: Array, default: () => [] },
  selectedIds: { type: Array, default: () => [] },
  /** `{ singular, plural }` noun for the copy. */
  entity: { type: Object, required: true },
  /** (row) => the row's identity in the summary list. */
  recordLabel: { type: Function, required: true },
  testidPrefix: { type: String, required: true },
  /** Store mutation in flight. */
  busy: { type: Boolean, default: false },
});

const emit = defineEmits(['close', 'submit']);

const isClient = computed(() => props.target === 'client');

const clientId = ref(null);
const clientLabel = ref('');
const projectId = ref(null);
const selectedProjectRow = ref(null);

/**
 * Selection frozen at open time. The page clears the selection right after a
 * successful submit, and reading it live would blank the plan while the
 * dialog is still transitioning out.
 */
const rowsSnapshot = ref([]);
const idsSnapshot = ref([]);

const selectedCount = computed(() => idsSnapshot.value.length);

const plan = computed(() => (isClient.value
  ? buildAssignmentPlan({
    rows: rowsSnapshot.value,
    selectedIds: idsSnapshot.value,
    mode: 'assign',
    targetClientId: clientId.value,
    targetClientLabel: clientLabel.value,
  })
  : buildProjectAssignmentPlan({
    rows: rowsSnapshot.value,
    selectedIds: idsSnapshot.value,
    mode: 'assign',
    targetProject: selectedProjectRow.value,
  })));

const hasTarget = computed(() => (
  isClient.value ? clientId.value != null : projectId.value != null
));

/** Empty string = the confirm button is live. */
const blockedReason = computed(() => {
  if (isClient.value) {
    if (!clientId.value) return 'Elige un cliente para poder asignar.';
    if (plan.value.affected.length === 0) {
      return `Todo lo seleccionado ya tiene a ${clientLabel.value}.`;
    }
    return '';
  }
  if (!projectId.value) return 'Elige un proyecto para poder asignar.';
  if (plan.value.affected.length > 0) return '';
  if (plan.value.blockedClientMismatch.length > 0) {
    return `La selección pertenece a otro cliente: "${plan.value.targetProjectLabel}" es de ${plan.value.targetClientLabel || 'otro cliente'}.`;
  }
  return `Todo lo seleccionado ya tiene "${plan.value.targetProjectLabel}".`;
});

/**
 * La razón de bloqueo sólo queda vacía cuando ya hay destino Y hay filas que
 * cambiar, así que el else es exactamente el caso en que corresponde
 * confirmar el enlace. Por eso la línea nunca está vacía.
 */
const statusLine = computed(() => {
  if (blockedReason.value) {
    return { text: blockedReason.value, icon: InformationCircleIcon };
  }
  if (isClient.value) {
    return {
      text: `Cliente enlazado: ${clientLabel.value} (#${clientId.value})`,
      icon: LinkIcon,
    };
  }
  const blocked = plan.value.blockedClientMismatch.length;
  const suffix = blocked > 0
    ? ` · ${blocked} de otro cliente no se ${blocked === 1 ? 'toca' : 'tocan'}`
    : '';
  return {
    text: `Proyecto enlazado: ${plan.value.targetProjectLabel} (#${projectId.value})${suffix}`,
    icon: LinkIcon,
  };
});

function onClientSelect(client) {
  clientLabel.value = client?.name || '';
}

function onProjectSelect(project) {
  selectedProjectRow.value = project || null;
}

// Typing in the picker drops the committed id without re-emitting `select`,
// so the label has to follow the id or the summary would name a target that
// is no longer chosen.
watch(clientId, (id) => {
  if (id == null) clientLabel.value = '';
});
watch(projectId, (id) => {
  if (id == null) selectedProjectRow.value = null;
});

// Every opening starts from scratch, and freezes the selection it will act on.
watch(() => props.open, (open) => {
  if (!open) return;
  clientId.value = null;
  clientLabel.value = '';
  projectId.value = null;
  selectedProjectRow.value = null;
  rowsSnapshot.value = [...props.rows];
  idsSnapshot.value = [...props.selectedIds];
}, { immediate: true });

/**
 * Hand the parent only the rows that actually change — the same ones the
 * summary listed, so the count reported afterwards matches what was promised.
 */
function confirm() {
  if (blockedReason.value || props.busy) return;
  const current = plan.value;
  emit('submit', isClient.value
    ? {
      ids: current.affected.map((row) => row.id),
      client: current.targetClientId,
      mode: 'assign',
      plan: current,
    }
    : {
      ids: current.affected.map((row) => row.id),
      project: current.targetProjectId,
      mode: 'assign',
      plan: current,
    });
  emit('close');
}
</script>
