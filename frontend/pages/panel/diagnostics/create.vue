<template>
  <div class="max-w-2xl mx-auto">
    <h1 class="text-2xl font-light text-gray-900 mb-6">Nuevo diagnóstico de aplicación</h1>

    <form class="space-y-6 bg-white rounded-xl border p-6" @submit.prevent="submit">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
        <input
          v-model="search"
          type="text"
          class="w-full border rounded px-3 py-2"
          placeholder="Buscar por nombre, email o empresa…"
          @input="onSearchInput"
        />
        <ul
          v-if="results.length && !selectedClient"
          class="mt-2 border rounded bg-white shadow max-h-60 overflow-auto divide-y"
        >
          <li
            v-for="c in results"
            :key="c.id"
            class="px-3 py-2 cursor-pointer hover:bg-emerald-50"
            @click="selectClient(c)"
          >
            <div class="font-medium">{{ clientLabel(c) }}</div>
            <div class="text-xs text-gray-500">{{ c.email || c.user?.email }}</div>
          </li>
        </ul>
        <div v-if="selectedClient" class="mt-2 p-3 bg-emerald-50 border border-emerald-200 rounded text-sm">
          <div class="font-medium">{{ clientLabel(selectedClient) }}</div>
          <div class="text-xs text-gray-600">{{ selectedClient.email || selectedClient.user?.email }}</div>
          <button type="button" class="mt-1 text-xs text-emerald-700 underline" @click="clearClient">
            Cambiar
          </button>
        </div>
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
          :disabled="!selectedClient || store.isUpdating"
        >
          {{ store.isUpdating ? 'Creando…' : 'Crear diagnóstico' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { get_request } from '~/stores/services/request_http';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const localePath = useLocalePath();
const router = useRouter();
const store = useDiagnosticsStore();

const search = ref('');
const results = ref([]);
const selectedClient = ref(null);
const language = ref('es');
const title = ref('');
const errorMsg = ref('');

let searchTimer = null;
function onSearchInput() {
  clearTimeout(searchTimer);
  if (!search.value.trim()) {
    results.value = [];
    return;
  }
  searchTimer = setTimeout(async () => {
    try {
      const response = await get_request(
        `proposals/client-profiles/search/?q=${encodeURIComponent(search.value)}`
      );
      results.value = response.data || [];
    } catch (_) {
      results.value = [];
    }
  }, 250);
}

onBeforeUnmount(() => clearTimeout(searchTimer));

function selectClient(c) {
  selectedClient.value = c;
  results.value = [];
  search.value = '';
}
function clearClient() {
  selectedClient.value = null;
  search.value = '';
}

function clientLabel(c) {
  return c.name || c.full_name || c.company || c.user?.email || '—';
}

async function submit() {
  errorMsg.value = '';
  const result = await store.create({
    client_id: selectedClient.value.id,
    language: language.value,
    title: title.value.trim(),
  });
  if (!result.success) {
    errorMsg.value = result.error || 'No se pudo crear el diagnóstico.';
    return;
  }
  router.push(localePath(`/panel/diagnostics/${result.data.id}/edit`));
}
</script>
