<template>
  <div class="min-h-screen bg-gray-50 py-10 px-4">
    <div class="max-w-4xl mx-auto">
      <header class="mb-8 text-center">
        <p class="text-xs font-semibold tracking-widest text-emerald-700 uppercase">Project App</p>
        <h1 class="text-3xl md:text-4xl font-light text-gray-900 mt-2">Diagnóstico de Aplicaciones Web</h1>
        <p v-if="store.current?.client_name" class="text-sm text-gray-500 mt-2">
          Preparado para {{ store.current.client_name }}
        </p>
      </header>

      <div v-if="store.isLoading" class="text-center text-gray-500">Cargando…</div>

      <div v-else-if="store.error === 'not_found'" class="text-center py-16">
        <p class="text-rose-600">Diagnóstico no encontrado.</p>
      </div>

      <template v-else-if="store.current">
        <nav v-if="docs.length > 1" class="flex flex-wrap justify-center gap-2 mb-6">
          <button
            v-for="(d, i) in docs"
            :key="d.id"
            class="px-4 py-2 rounded-full text-sm border"
            :class="activeDoc === i
              ? 'bg-emerald-600 text-white border-emerald-600'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'"
            @click="activeDoc = i"
          >{{ d.title }}</button>
        </nav>

        <article class="bg-white rounded-2xl shadow-sm border p-6 md:p-12">
          <DiagnosticDocumentViewer :markdown="docs[activeDoc]?.rendered_md || ''" />
        </article>

        <footer
          v-if="canRespond"
          class="mt-8 bg-white rounded-2xl border p-6 text-center"
        >
          <p class="text-gray-700 mb-4">¿Quieres avanzar con el diagnóstico?</p>
          <div class="flex justify-center gap-3">
            <button
              class="px-6 py-3 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 disabled:opacity-50"
              :disabled="store.isUpdating"
              @click="respond('accept')"
            >Aceptar propuesta</button>
            <button
              class="px-6 py-3 border border-rose-300 text-rose-700 rounded-xl hover:bg-rose-50 disabled:opacity-50"
              :disabled="store.isUpdating"
              @click="respond('reject')"
            >No por ahora</button>
          </div>
          <p v-if="responseMsg" class="mt-4 text-sm text-gray-600">{{ responseMsg }}</p>
        </footer>

        <footer
          v-else-if="store.current.status === DIAGNOSTIC_STATUS.ACCEPTED"
          class="mt-8 bg-emerald-50 border border-emerald-200 rounded-2xl p-6 text-center text-emerald-800"
        >
          ¡Gracias! Confirmamos tu aceptación. Te contactaremos para coordinar el inicio.
        </footer>

        <footer
          v-else-if="store.current.status === DIAGNOSTIC_STATUS.REJECTED"
          class="mt-8 bg-rose-50 border border-rose-200 rounded-2xl p-6 text-center text-rose-800"
        >
          Recibimos tu respuesta. Si cambias de opinión, contáctanos cuando quieras.
        </footer>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useDiagnosticsStore } from '~/stores/diagnostics';
import { DIAGNOSTIC_STATUS } from '~/stores/diagnostics_constants';
import DiagnosticDocumentViewer from '~/components/WebAppDiagnostic/DiagnosticDocumentViewer.vue';

definePageMeta({ layout: 'default' });

const route = useRoute();
const store = useDiagnosticsStore();
const activeDoc = ref(0);
const responseMsg = ref('');

const docs = computed(() => store.current?.documents || []);

const canRespond = computed(() => (
  store.current?.status === DIAGNOSTIC_STATUS.SENT
  && !!store.current?.final_sent_at
));

async function respond(decision) {
  responseMsg.value = '';
  const r = await store.respondPublic(route.params.uuid, decision);
  if (r.success) {
    responseMsg.value = decision === 'accept'
      ? 'Tu aceptación quedó registrada.'
      : 'Tu respuesta quedó registrada.';
  } else {
    responseMsg.value = 'No pudimos registrar tu respuesta. Por favor inténtalo nuevamente.';
  }
}

onMounted(async () => {
  await store.fetchPublic(route.params.uuid);
  store.trackView(route.params.uuid);
});
</script>
