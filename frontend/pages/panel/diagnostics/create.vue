<template>
  <div class="max-w-2xl mx-auto">
    <header class="mb-6">
      <NuxtLink
        :to="localePath('/panel/diagnostics')"
        class="text-sm text-text-muted hover:underline"
      >← Diagnósticos</NuxtLink>
      <h1 class="text-2xl font-light text-text-default mt-1">Nuevo diagnóstico de aplicación</h1>
      <p class="text-sm text-text-muted mt-1">
        Crea un diagnóstico para un cliente existente. Podrás completar pricing, radiografía y documentos después.
      </p>
    </header>

    <form
      class="bg-surface rounded-2xl shadow-sm border border-border-muted p-6 space-y-6"
      @submit.prevent="submit"
    >
      <BaseFormField
        label="Cliente"
        hint="Busca por nombre, email o empresa. Solo clientes existentes pueden recibir un diagnóstico."
      >
        <ClientAutocomplete
          v-model="selectedClientId"
          placeholder="Buscar cliente por nombre, email o empresa..."
          test-id="diagnostic-client-autocomplete"
          @select="onClientSelected"
        />
      </BaseFormField>

      <BaseFormField label="Idioma">
        <BaseSelect
          v-model="language"
          :options="[
            { value: 'es', label: 'Español' },
            { value: 'en', label: 'English' },
          ]"
        />
      </BaseFormField>

      <BaseFormField label="Título (opcional)">
        <BaseInput
          v-model="title"
          placeholder="Se generará automáticamente si lo dejas vacío"
        />
      </BaseFormField>

      <BaseAlert v-if="errorMsg" variant="danger">{{ errorMsg }}</BaseAlert>

      <div class="text-right">
        <BaseButton
          type="submit"
          variant="primary"
          :loading="store.isUpdating"
          :disabled="!selectedClientId || store.isUpdating"
          data-testid="diagnostic-submit-btn"
        >
          Crear diagnóstico
        </BaseButton>
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

const FALLBACK_ERROR = 'No se pudo crear el diagnóstico. Verifica tu sesión e inténtalo de nuevo.';

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
    errorMsg.value = 'Selecciona un cliente antes de continuar.';
    return;
  }
  const result = await store.create({
    client_id: selectedClientId.value,
    language: language.value,
    title: title.value.trim(),
  });
  if (!result.success) {
    errorMsg.value = result.message || FALLBACK_ERROR;
    return;
  }
  router.push(localePath(`/panel/diagnostics/${result.data.id}/edit`));
}
</script>
