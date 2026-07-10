<template>
  <BaseModal :model-value="open" size="xl" title-id="hosting-cycles-title" @close="emit('close')">
    <div class="px-6 pt-6 pb-2">
      <h3 id="hosting-cycles-title" class="text-lg font-bold text-text-default">
        Ciclos de pago — {{ record?.client_name }}
      </h3>
      <p class="text-sm text-text-muted mt-1">
        El total pagado del hosting es la suma de este histórico
        ({{ formatMoney(record?.total_paid ?? 0, 'COP') }} en
        {{ record?.cycles_count ?? 0 }} ciclo{{ (record?.cycles_count ?? 0) === 1 ? '' : 's' }}).
      </p>
    </div>

    <div class="px-6 py-4 space-y-5">
      <!-- Register form -->
      <form
        class="bg-surface-raised rounded-xl p-4 grid grid-cols-1 sm:grid-cols-2 gap-4"
        @submit.prevent="submit"
      >
        <BaseFormField label="Monto pagado" required>
          <BaseCurrencyInput v-model="form.amount" required data-testid="cycle-amount" />
        </BaseFormField>
        <BaseFormField label="Modalidad del ciclo">
          <BaseSelect v-model="form.modality" :options="modalityOptions" />
        </BaseFormField>
        <BaseFormField label="Fecha de pago">
          <BaseInput v-model="form.paid_at" type="date" />
        </BaseFormField>
        <BaseFormField label="Notas">
          <BaseInput v-model="form.notes" placeholder="Opcional" />
        </BaseFormField>
        <div class="sm:col-span-2 flex flex-wrap items-center justify-between gap-3">
          <label class="flex items-center gap-2 text-sm text-text-default">
            <BaseToggle v-model="form.advance_validity" aria-label="Extender vigencia" />
            <span>
              Extender vigencia
              <span v-if="projectedValidTo" class="text-text-muted">hasta {{ projectedValidTo }}</span>
            </span>
          </label>
          <BaseButton type="submit" variant="primary" :disabled="saving" data-testid="cycle-submit">
            {{ saving ? 'Registrando...' : 'Registrar pago de ciclo' }}
          </BaseButton>
        </div>
      </form>

      <!-- History -->
      <div>
        <p class="text-xs font-semibold text-text-subtle uppercase tracking-wider mb-2">Histórico</p>
        <p v-if="loading" class="text-sm text-text-subtle py-4">Cargando ciclos...</p>
        <p v-else-if="cycles.length === 0" class="text-sm text-text-subtle py-4">
          Sin ciclos registrados todavía.
        </p>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs text-text-subtle uppercase tracking-wider">
                <th class="px-3 py-2">Pago</th>
                <th class="px-3 py-2">Modalidad</th>
                <th class="px-3 py-2">Período</th>
                <th class="px-3 py-2 text-right">Monto</th>
                <th class="px-3 py-2 text-right"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="cycle in cycles"
                :key="cycle.id"
                class="border-t border-border-muted"
              >
                <td class="px-3 py-2 whitespace-nowrap">{{ cycle.paid_at }}</td>
                <td class="px-3 py-2">
                  {{ cycle.modality_label }}
                  <span
                    v-if="cycle.is_backfill"
                    class="ml-1 text-[10px] px-1.5 py-0.5 rounded-full bg-surface-raised text-text-muted"
                    :title="cycle.notes"
                  >
                    histórico × {{ cycle.cycles_represented }}
                  </span>
                </td>
                <td class="px-3 py-2 text-text-muted text-xs whitespace-nowrap">
                  {{ cycle.period_from || '—' }} → {{ cycle.period_to || '—' }}
                </td>
                <td class="px-3 py-2 text-right tabular-nums">
                  {{ formatMoney(cycle.amount, 'COP') }}
                </td>
                <td class="px-3 py-2 text-right">
                  <button
                    type="button"
                    aria-label="Eliminar ciclo"
                    class="p-1.5 rounded-lg text-text-subtle hover:text-danger-strong hover:bg-danger-soft transition-colors"
                    @click="askDelete(cycle)"
                  >
                    <TrashIcon class="w-4 h-4" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="flex items-center justify-end pt-2">
        <BaseButton type="button" variant="secondary" @click="emit('close')">Cerrar</BaseButton>
      </div>
    </div>

    <ConfirmModal
      v-model="deleteConfirmOpen"
      title="Eliminar ciclo"
      :message="deleteMessage"
      confirm-text="Eliminar"
      cancel-text="Cancelar"
      variant="danger"
      @confirm="confirmDelete"
      @cancel="cycleToDelete = null"
    />
  </BaseModal>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { TrashIcon } from '@heroicons/vue/24/outline';
import ConfirmModal from '~/components/ConfirmModal.vue';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useAccountingStore } from '~/stores/accounting';
import { formatMoney } from '~/utils/formatMoney';

const props = defineProps({
  open: { type: Boolean, default: false },
  record: { type: Object, default: null },
});

const emit = defineEmits(['close', 'changed']);

const store = useAccountingStore();
const notify = usePanelNotify();

const MODALITY_MONTHS = { monthly: 1, quarterly: 3, semiannual: 6, annual: 12 };

const modalityOptions = [
  { value: 'monthly', label: 'Mensual' },
  { value: 'quarterly', label: 'Trimestral' },
  { value: 'semiannual', label: 'Semestral' },
  { value: 'annual', label: 'Anual' },
];

const cycles = ref([]);
const loading = ref(false);
const saving = ref(false);

function defaultForm() {
  return {
    amount: props.record ? Number(props.record.payment_per_cycle) || null : null,
    modality: props.record?.payment_modality || 'monthly',
    paid_at: new Date().toISOString().slice(0, 10),
    notes: '',
    advance_validity: true,
  };
}

const form = ref(defaultForm());

const projectedValidTo = computed(() => {
  const base = props.record?.valid_to;
  if (!base) return '';
  const months = MODALITY_MONTHS[form.value.modality] || 1;
  const [year, month, day] = base.split('-').map(Number);
  const target = new Date(Date.UTC(year, month - 1 + months, day));
  return target.toISOString().slice(0, 10);
});

async function loadCycles() {
  if (!props.record) return;
  loading.value = true;
  const result = await store.fetchHostingCycles(props.record.id);
  loading.value = false;
  if (result.success) {
    cycles.value = result.data;
  } else {
    notify.error({ title: 'No se pudieron cargar los ciclos', detail: result.message });
  }
}

watch(
  () => [props.open, props.record?.id],
  () => {
    if (!props.open) return;
    form.value = defaultForm();
    loadCycles();
  },
  { immediate: true },
);

async function submit() {
  if (!props.record || !form.value.amount) return;
  saving.value = true;
  const result = await store.createHostingCycle(props.record.id, {
    amount: form.value.amount,
    modality: form.value.modality,
    paid_at: form.value.paid_at,
    notes: form.value.notes,
    advance_validity: form.value.advance_validity,
  });
  saving.value = false;
  if (result.success) {
    notify.success({ title: 'Pago de ciclo registrado' });
    form.value = defaultForm();
    loadCycles();
    emit('changed');
  } else {
    notify.error({ title: 'No se pudo registrar el ciclo', detail: result.message });
  }
}

const deleteConfirmOpen = ref(false);
const cycleToDelete = ref(null);

const deleteMessage = computed(() => {
  const cycle = cycleToDelete.value;
  if (!cycle) return '';
  return (
    `Se eliminará el ciclo del ${cycle.paid_at} por ${formatMoney(cycle.amount, 'COP')} ` +
    'y se recalculará el total pagado. La vigencia del hosting no se revierte.'
  );
});

function askDelete(cycle) {
  cycleToDelete.value = cycle;
  deleteConfirmOpen.value = true;
}

async function confirmDelete() {
  const cycle = cycleToDelete.value;
  cycleToDelete.value = null;
  if (!cycle || !props.record) return;
  const result = await store.deleteHostingCycle(props.record.id, cycle.id);
  if (result.success) {
    notify.success({ title: 'Ciclo eliminado' });
    loadCycles();
    emit('changed');
  } else {
    notify.error({ title: 'No se pudo eliminar el ciclo', detail: result.message });
  }
}
</script>
