<template>
  <div class="max-w-2xl mx-auto">
    <h1 class="text-2xl font-light text-gray-900 mb-6">Nuevo diagnóstico de aplicación</h1>

    <form class="space-y-6 bg-white rounded-xl border p-6" @submit.prevent="submit">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
        <ClientAutocomplete
          v-model="selectedClientId"
          placeholder="Buscar cliente por nombre, email o empresa..."
          test-id="diagnostic-client-autocomplete"
          @select="onClientSelected"
        />
        <p class="text-xs text-gray-500 mt-1">
          Busca por nombre, email o empresa. Solo clientes existentes pueden recibir un diagnóstico.
        </p>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
        <select v-model="language" class="w-full border rounded px-3 py-2">
          <option value="es">Español</option>
          <option value="en">English</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Título (opcional)</label>
        <input
          v-model="title"
          type="text"
          class="w-full border rounded px-3 py-2"
          placeholder="Se generará automáticamente si lo dejas vacío"
        />
      </div>

      <div v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</div>

      <div class="text-right">
        <button
          type="submit"
          class="px-5 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:opacity-50"
          :disabled="!selectedClientId || store.isUpdating"
          data-testid="diagnostic-submit-btn"
        >
          {{ store.isUpdating ? 'Creando…' : 'Crear diagnóstico' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const localePath = useLocalePath();
const router = useRouter();
const store = useDiagnosticsStore();

const selectedClientId = ref(null);
const language = ref('es');
const title = ref('');
const errorMsg = ref('');

const BACKEND_ERROR_MESSAGES = {
  client_id_required: 'Selecciona un cliente antes de continuar.',
  client_not_found: 'El cliente seleccionado no existe o no tiene rol de cliente.',
  create_failed: 'No se pudo crear el diagnóstico. Verifica tu sesión e inténtalo de nuevo.',
};

function onClientSelected(client) {
  errorMsg.value = '';
  if (client && !title.value.trim()) {
    const clientName = client.name || client.company || client.email || '';
    if (clientName) title.value = `Diagnóstico — ${clientName}`;
  }
}

async function submit() {
  errorMsg.value = '';
  if (!selectedClientId.value) {
    errorMsg.value = BACKEND_ERROR_MESSAGES.client_id_required;
    return;
  }
  const result = await store.create({
    client_id: selectedClientId.value,
    language: language.value,
    title: title.value.trim(),
  });
  if (!result.success) {
    errorMsg.value = BACKEND_ERROR_MESSAGES[result.error] || result.error || BACKEND_ERROR_MESSAGES.create_failed;
    return;
  }
  router.push(localePath(`/panel/diagnostics/${result.data.id}/edit`));
}
</script>
