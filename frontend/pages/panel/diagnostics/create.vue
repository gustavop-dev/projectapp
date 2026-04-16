<template>
  <div class="max-w-2xl mx-auto">
    <header class="mb-6">
      <NuxtLink
        :to="localePath('/panel/diagnostics')"
        class="text-sm text-gray-500 dark:text-gray-400 hover:underline"
      >← Diagnósticos</NuxtLink>
      <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100 mt-1">Nuevo diagnóstico de aplicación</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        Crea un diagnóstico para un cliente existente. Podrás completar pricing, radiografía y documentos después.
      </p>
    </header>

    <form
      class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-6
             dark:bg-gray-800 dark:border-gray-700"
      @submit.prevent="submit"
    >
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cliente</label>
        <ClientAutocomplete
          v-model="selectedClientId"
          placeholder="Buscar cliente por nombre, email o empresa..."
          test-id="diagnostic-client-autocomplete"
          @select="onClientSelected"
        />
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Busca por nombre, email o empresa. Solo clientes existentes pueden recibir un diagnóstico.
        </p>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Idioma</label>
        <select
          v-model="language"
          class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm bg-white outline-none
                 focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500
                 dark:bg-gray-900 dark:border-gray-600 dark:text-gray-200"
        >
          <option value="es">Español</option>
          <option value="en">English</option>
        </select>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título (opcional)</label>
        <input
          v-model="title"
          type="text"
          class="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm outline-none
                 focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500
                 dark:bg-gray-900 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500"
          placeholder="Se generará automáticamente si lo dejas vacío"
        />
      </div>

      <div
        v-if="errorMsg"
        class="rounded-xl bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 text-sm
               dark:bg-rose-900/20 dark:border-rose-700 dark:text-rose-300"
      >{{ errorMsg }}</div>

      <div class="text-right">
        <button
          type="submit"
          class="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-xl
                 font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50
                 dark:bg-emerald-700 dark:hover:bg-emerald-600"
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
