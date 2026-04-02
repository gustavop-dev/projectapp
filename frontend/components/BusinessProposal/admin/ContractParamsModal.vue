<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50" @click="$emit('cancel')" />

        <!-- Modal -->
        <div class="relative bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div class="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 rounded-t-2xl z-10">
            <h2 class="text-lg font-semibold text-gray-900">
              {{ isEditing ? 'Editar contrato de desarrollo' : 'Generar contrato de desarrollo' }}
            </h2>
            <p class="text-xs text-gray-500 mt-1">
              Revisa y completa los datos del contrato. Los campos del contratista se pre-cargan desde la configuración de la empresa.
            </p>
          </div>

          <form class="px-6 py-5 space-y-6" @submit.prevent="handleSubmit">
            <!-- Contractor (seller) section -->
            <fieldset>
              <legend class="text-sm font-semibold text-emerald-700 mb-3">EL CONTRATISTA (tu empresa)</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Nombre completo</label>
                  <input v-model="form.contractor_full_name" type="text" required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Cédula</label>
                  <input v-model="form.contractor_cedula" type="text" required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Email de notificación</label>
                  <input v-model="form.contractor_email" type="email" required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Ciudad del contrato</label>
                  <input v-model="form.contract_city" type="text" required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Banco</label>
                  <input v-model="form.bank_name" type="text" required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Tipo de cuenta</label>
                  <select v-model="form.bank_account_type"
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500">
                    <option value="Ahorros">Ahorros</option>
                    <option value="Corriente">Corriente</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Número de cuenta</label>
                  <input v-model="form.bank_account_number" type="text" required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
              </div>
            </fieldset>

            <!-- Client (contratante) section -->
            <fieldset>
              <legend class="text-sm font-semibold text-emerald-700 mb-3">EL CONTRATANTE (cliente)</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Nombre completo</label>
                  <input v-model="form.client_full_name" type="text" required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Cédula *</label>
                  <input v-model="form.client_cedula" type="text" required placeholder="Ej: 1.234.567.890"
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
                <div class="sm:col-span-2">
                  <label class="block text-xs text-gray-500 mb-1">Email de notificación</label>
                  <input v-model="form.client_email" type="email" required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
              </div>
            </fieldset>

            <!-- Contract metadata -->
            <fieldset>
              <legend class="text-sm font-semibold text-emerald-700 mb-3">Datos del contrato</legend>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">Fecha del contrato</label>
                  <input v-model="form.contract_date" type="date" required
                    class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500" />
                </div>
              </div>
            </fieldset>

            <!-- Actions -->
            <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-100">
              <button type="button" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors" @click="$emit('cancel')">
                Cancelar
              </button>
              <button type="submit" :disabled="saving"
                class="px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50">
                {{ saving ? 'Generando...' : (isEditing ? 'Actualizar contrato' : 'Generar contrato y negociar') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  proposal: { type: Object, default: () => ({}) },
  initialParams: { type: Object, default: () => ({}) },
  isEditing: { type: Boolean, default: false },
  saving: { type: Boolean, default: false },
});

const emit = defineEmits(['confirm', 'cancel']);

const proposalStore = useProposalStore();
const companyDefaults = ref({});

const form = ref({
  contractor_full_name: '',
  contractor_cedula: '',
  contractor_email: '',
  bank_name: '',
  bank_account_type: 'Ahorros',
  bank_account_number: '',
  contract_city: 'Medellín',
  client_full_name: '',
  client_cedula: '',
  client_email: '',
  contract_date: new Date().toISOString().slice(0, 10),
});

async function loadDefaults() {
  const result = await proposalStore.fetchCompanySettings();
  if (result.success) {
    companyDefaults.value = result.data;
  }
}

function resetForm() {
  const defaults = companyDefaults.value;
  const existing = props.initialParams || {};
  const p = props.proposal || {};

  form.value = {
    contractor_full_name: existing.contractor_full_name || defaults.contractor_full_name || '',
    contractor_cedula: existing.contractor_cedula || defaults.contractor_cedula || '',
    contractor_email: existing.contractor_email || defaults.contractor_email || '',
    bank_name: existing.bank_name || defaults.bank_name || '',
    bank_account_type: existing.bank_account_type || defaults.bank_account_type || 'Ahorros',
    bank_account_number: existing.bank_account_number || defaults.bank_account_number || '',
    contract_city: existing.contract_city || defaults.contract_city || 'Medellín',
    client_full_name: existing.client_full_name || p.client_name || '',
    client_cedula: existing.client_cedula || '',
    client_email: existing.client_email || p.client_email || '',
    contract_date: existing.contract_date || new Date().toISOString().slice(0, 10),
  };
}

watch(() => props.visible, async (val) => {
  if (val) {
    if (!companyDefaults.value.contractor_full_name) {
      await loadDefaults();
    }
    resetForm();
  }
});

onMounted(loadDefaults);

function handleSubmit() {
  emit('confirm', { ...form.value });
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
