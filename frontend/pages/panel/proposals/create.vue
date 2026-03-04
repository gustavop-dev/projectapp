<template>
  <div>
    <div class="mb-8">
      <NuxtLink to="/panel/proposals" class="text-sm text-gray-500 hover:text-gray-700 transition-colors">
        ← Volver a propuestas
      </NuxtLink>
      <h1 class="text-2xl font-light text-gray-900 mt-2">Nueva Propuesta</h1>
    </div>

    <form class="bg-white rounded-xl shadow-sm border border-gray-100 p-8 max-w-2xl" @submit.prevent="handleSubmit">
      <div class="space-y-6">
        <!-- Title -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Título</label>
          <input
            v-model="form.title"
            type="text"
            required
            placeholder="Propuesta Desarrollo Web — Cliente"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
        </div>

        <!-- Client name -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Nombre del cliente</label>
          <input
            v-model="form.client_name"
            type="text"
            required
            placeholder="María García"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
        </div>

        <!-- Client email -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email del cliente</label>
          <input
            v-model="form.client_email"
            type="email"
            placeholder="maria@example.com"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
        </div>

        <!-- Investment + Currency -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Inversión total</label>
            <input
              v-model.number="form.total_investment"
              type="number"
              min="0"
              step="0.01"
              placeholder="3500000"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Moneda</label>
            <select
              v-model="form.currency"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white"
            >
              <option value="COP">COP</option>
              <option value="USD">USD</option>
            </select>
          </div>
        </div>

        <!-- Expires at -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Fecha de expiración</label>
          <input
            v-model="form.expires_at"
            type="datetime-local"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
        </div>

        <!-- Reminder days -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Días para recordatorio</label>
          <input
            v-model.number="form.reminder_days"
            type="number"
            min="1"
            max="30"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
          <p class="text-xs text-gray-400 mt-1">Después de enviar la propuesta, se enviará un email recordatorio al cliente.</p>
        </div>

        <!-- Discount -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descuento (%)</label>
          <input
            v-model.number="form.discount_percent"
            type="number"
            min="0"
            max="100"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
          <p class="text-xs text-gray-400 mt-1">Si es mayor a 0, se enviará un email de urgencia con descuento 2 días antes de expirar. 0 = sin descuento.</p>
        </div>

        <!-- Errors -->
        <div v-if="errorMsg" class="text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl">
          {{ errorMsg }}
        </div>

        <!-- Submit -->
        <div class="flex items-center gap-4 pt-2">
          <button
            type="submit"
            :disabled="proposalStore.isUpdating"
            class="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                   hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
          >
            {{ proposalStore.isUpdating ? 'Creando...' : 'Crear Propuesta' }}
          </button>
          <NuxtLink to="/panel/proposals" class="text-sm text-gray-500 hover:text-gray-700">
            Cancelar
          </NuxtLink>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const router = useRouter();
const proposalStore = useProposalStore();
const errorMsg = ref('');

// Default expires_at: 7 days from now
const defaultExpiry = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
const pad = (n) => String(n).padStart(2, '0');
const defaultExpiryStr = `${defaultExpiry.getFullYear()}-${pad(defaultExpiry.getMonth() + 1)}-${pad(defaultExpiry.getDate())}T${pad(defaultExpiry.getHours())}:${pad(defaultExpiry.getMinutes())}`;

const form = reactive({
  title: '',
  client_name: '',
  client_email: '',
  total_investment: 0,
  currency: 'COP',
  expires_at: defaultExpiryStr,
  reminder_days: 5,
  discount_percent: 20,
});

async function handleSubmit() {
  errorMsg.value = '';

  const payload = { ...form };
  if (payload.expires_at) {
    payload.expires_at = new Date(payload.expires_at).toISOString();
  }

  const result = await proposalStore.createProposal(payload);
  if (result.success) {
    router.push(`/panel/proposals/${result.data.id}/edit`);
  } else {
    const errors = result.errors;
    if (errors && typeof errors === 'object') {
      errorMsg.value = Object.entries(errors)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
        .join(' | ');
    } else {
      errorMsg.value = 'Error al crear la propuesta.';
    }
  }
}
</script>
