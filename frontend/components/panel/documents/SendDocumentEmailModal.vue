<template>
  <Teleport to="body">
    <Transition name="fade-modal">
      <div
        v-if="modelValue && document"
        class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        @click.self="close"
      >
        <div class="bg-surface rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">

          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-border-muted flex-shrink-0">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-8 h-8 rounded-lg bg-primary-soft flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="min-w-0">
                <h3 class="text-base font-semibold text-text-default">Enviar por correo</h3>
                <p class="text-xs text-text-muted truncate">{{ document.title }}</p>
              </div>
            </div>
            <button
              type="button"
              class="w-8 h-8 flex-shrink-0 ml-2 flex items-center justify-center rounded-lg text-text-subtle hover:text-text-muted hover:bg-surface-raised transition-colors"
              @click="close"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Tab switcher -->
          <div class="flex gap-4 border-b border-border-muted px-6 flex-shrink-0">
            <button
              type="button"
              class="pb-3 pt-2 text-sm transition-colors border-b-2"
              :class="activeTab === 'edit'
                ? 'border-emerald-600 text-text-brand font-semibold'
                : 'border-transparent text-text-muted hover:text-text-default'"
              @click="activeTab = 'edit'"
            >
              Editar
            </button>
            <button
              type="button"
              class="pb-3 pt-2 text-sm transition-colors border-b-2"
              :class="activeTab === 'preview'
                ? 'border-emerald-600 text-text-brand font-semibold'
                : 'border-transparent text-text-muted hover:text-text-default'"
              @click="activeTab = 'preview'"
            >
              Vista previa
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto px-6 py-5">

            <!-- ── EDIT ── -->
            <div v-if="activeTab === 'edit'" class="space-y-4">
              <!-- Recipient -->
              <div>
                <label class="block text-xs text-text-muted mb-1">Para</label>
                <input
                  v-model="recipient"
                  type="email"
                  placeholder="correo@ejemplo.com"
                  class="bg-input-bg w-full px-3 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm text-text-default focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
                />
              </div>

              <!-- Subject -->
              <div>
                <label class="block text-xs text-text-muted mb-1">Asunto</label>
                <input
                  v-model="subject"
                  type="text"
                  placeholder="Asunto del correo"
                  class="bg-input-bg w-full px-3 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm text-text-default focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
                />
              </div>

              <!-- Greeting -->
              <div>
                <label class="block text-xs text-text-muted mb-1">Saludo</label>
                <input
                  v-model="greeting"
                  type="text"
                  placeholder="Hola Carlos"
                  class="bg-input-bg w-full px-3 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm text-text-default focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
                />
              </div>

              <!-- Sections -->
              <div>
                <label class="block text-xs text-text-muted mb-2">Secciones del correo</label>
                <div class="space-y-3">
                  <div
                    v-for="(section, idx) in sections"
                    :key="section.id"
                    class="bg-surface-raised rounded-lg p-3 border border-border-muted"
                  >
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-[10px] text-text-subtle uppercase tracking-wide">Sección {{ idx + 1 }}</span>
                      <div class="ml-auto flex items-center gap-1">
                        <button
                          type="button"
                          class="p-1 rounded text-text-subtle hover:text-text-default hover:bg-surface-muted disabled:opacity-30 disabled:cursor-not-allowed"
                          :disabled="idx === 0"
                          title="Subir"
                          @click="moveSection(idx, -1)"
                        >
                          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                          </svg>
                        </button>
                        <button
                          type="button"
                          class="p-1 rounded text-text-subtle hover:text-text-default hover:bg-surface-muted disabled:opacity-30 disabled:cursor-not-allowed"
                          :disabled="idx === sections.length - 1"
                          title="Bajar"
                          @click="moveSection(idx, 1)"
                        >
                          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                        <button
                          v-if="sections.length > 1"
                          type="button"
                          class="p-1 rounded text-text-subtle hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                          title="Eliminar sección"
                          @click="removeSection(idx)"
                        >
                          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                    <textarea
                      v-model="section.text"
                      rows="3"
                      placeholder="Escribe el contenido de esta sección..."
                      class="bg-input-bg w-full px-3 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm text-text-default focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-y"
                    />
                  </div>
                </div>
                <button
                  type="button"
                  class="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-brand bg-primary-soft rounded-lg hover:bg-primary-soft transition-colors"
                  @click="addSection"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                  Agregar sección
                </button>
              </div>

              <!-- Footer text -->
              <div>
                <label class="block text-xs text-text-muted mb-1">Pie de correo</label>
                <textarea
                  v-model="footer"
                  rows="2"
                  placeholder="Saludos cordiales..."
                  class="bg-input-bg w-full px-3 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm text-text-default focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-y"
                />
              </div>

              <!-- Attachments -->
              <div>
                <label class="block text-xs text-text-muted mb-2">Documentos adjuntos (PDF)</label>
                <div class="space-y-1.5">
                  <div
                    v-for="docId in selectedDocIds"
                    :key="docId"
                    class="flex items-center gap-2 px-3 py-2 bg-surface-raised rounded-lg border border-border-muted text-sm"
                  >
                    <svg class="w-4 h-4 text-text-subtle flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span class="flex-1 min-w-0 truncate text-text-default">{{ docTitle(docId) }}.pdf</span>
                    <button
                      v-if="docId !== document.id"
                      type="button"
                      class="p-1 rounded text-text-subtle hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
                      title="Quitar"
                      @click="removeAttachment(docId)"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    <span v-else class="text-[10px] uppercase tracking-wide text-text-subtle">Principal</span>
                  </div>
                </div>
                <button
                  type="button"
                  class="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-text-brand bg-primary-soft rounded-lg hover:bg-primary-soft transition-colors"
                  @click="showPicker = true"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                  Adjuntar otro documento
                </button>

                <!-- Picker -->
                <div
                  v-if="showPicker"
                  class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
                  @click.self="showPicker = false"
                >
                  <div class="bg-surface rounded-xl shadow-xl max-w-md w-full max-h-[70vh] flex flex-col border border-border-default">
                    <header class="flex items-center justify-between px-5 py-3 border-b border-border-muted">
                      <h4 class="text-sm font-semibold text-text-default">Seleccionar documentos</h4>
                      <button type="button" class="text-text-subtle hover:text-text-default" @click="showPicker = false">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </header>
                    <div class="flex-1 overflow-y-auto px-5 py-3">
                      <p v-if="!availableDocs.length" class="text-xs text-text-subtle py-6 text-center">
                        No hay otros documentos disponibles para adjuntar.
                      </p>
                      <ul v-else class="divide-y divide-border-muted">
                        <li v-for="d in availableDocs" :key="d.id" class="py-2 flex items-center gap-3">
                          <input
                            :id="`pick-${d.id}`"
                            v-model="selectedDocIds"
                            type="checkbox"
                            :value="d.id"
                            class="rounded border-input-border text-text-brand focus:ring-focus-ring/30"
                          />
                          <label :for="`pick-${d.id}`" class="flex-1 min-w-0 cursor-pointer">
                            <div class="text-sm text-text-default truncate">{{ d.title }}</div>
                            <div v-if="d.folder_name" class="text-[11px] text-text-subtle mt-0.5">📁 {{ d.folder_name }}</div>
                          </label>
                        </li>
                      </ul>
                    </div>
                    <footer class="px-5 py-3 border-t border-border-muted flex justify-end">
                      <button
                        type="button"
                        class="px-4 py-1.5 text-xs font-medium bg-primary text-white rounded-lg hover:bg-primary-strong"
                        @click="showPicker = false"
                      >
                        Listo
                      </button>
                    </footer>
                  </div>
                </div>
              </div>
            </div>

            <!-- ── PREVIEW ── -->
            <div v-else class="bg-surface border border-border-muted rounded-lg p-6 text-text-default">
              <div class="text-xs text-text-subtle mb-1"><strong>Para:</strong> {{ recipient || '—' }}</div>
              <div class="text-xs text-text-subtle mb-4"><strong>Asunto:</strong> {{ subject || '—' }}</div>
              <hr class="border-border-muted mb-4" />
              <p v-if="greeting" class="mb-3 text-sm">{{ greeting }}</p>
              <p
                v-for="section in sections"
                :key="`prev-${section.id}`"
                class="mb-3 text-sm whitespace-pre-wrap"
              >
                {{ section.text }}
              </p>
              <p v-if="footer" class="mt-4 pt-3 border-t border-border-muted text-sm whitespace-pre-wrap text-text-muted">
                {{ footer }}
              </p>
              <div v-if="selectedDocIds.length" class="mt-4 pt-3 border-t border-border-muted">
                <p class="text-xs text-text-subtle mb-1.5">Adjuntos:</p>
                <ul class="space-y-1">
                  <li v-for="docId in selectedDocIds" :key="`prev-att-${docId}`" class="text-xs text-text-default flex items-center gap-2">
                    <svg class="w-3.5 h-3.5 text-text-subtle" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    {{ docTitle(docId) }}.pdf
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Error / status -->
          <div v-if="errorMsg || successMsg" class="px-6 pb-2 flex-shrink-0">
            <p
              v-if="errorMsg"
              class="text-xs px-3 py-2 rounded-lg"
              :class="rateLimited
                ? 'text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20'
                : 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'"
            >
              {{ errorMsg }}
            </p>
            <p v-else-if="successMsg" class="text-xs text-emerald-700 dark:text-emerald-400 bg-success-soft px-3 py-2 rounded-lg">
              {{ successMsg }}
            </p>
          </div>

          <!-- Footer buttons -->
          <div class="px-6 py-4 border-t border-border-muted flex justify-end gap-2 flex-shrink-0">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-text-muted hover:text-text-default hover:bg-surface-raised rounded-lg transition-colors"
              @click="close"
            >
              Cancelar
            </button>
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary-strong transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!canSend || isSending"
              @click="send"
            >
              {{ isSending ? 'Enviando...' : 'Enviar' }}
            </button>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  document: { type: Object, default: null },
});
const emit = defineEmits(['update:modelValue', 'sent']);

const documentStore = useDocumentStore();

const activeTab = ref('edit');
const recipient = ref('');
const subject = ref('');
const greeting = ref('');
const footer = ref('');
const sections = ref([{ id: 1, text: '' }]);
const selectedDocIds = ref([]);
const showPicker = ref(false);
const isSending = ref(false);
const errorMsg = ref('');
const successMsg = ref('');
const rateLimited = ref(false);

let nextSectionId = 2;

const canSend = computed(() => {
  if (!recipient.value.trim() || !subject.value.trim()) return false;
  return sections.value.some((s) => s.text.trim().length > 0);
});

const availableDocs = computed(() => {
  if (!props.document) return [];
  return documentStore.documents.filter((d) => d.id !== props.document.id);
});

watch(
  () => [props.modelValue, props.document],
  async ([open, doc]) => {
    if (!open || !doc) return;
    activeTab.value = 'edit';
    recipient.value = '';
    subject.value = doc.title || '';
    sections.value = [{ id: 1, text: '' }];
    nextSectionId = 2;
    selectedDocIds.value = [doc.id];
    errorMsg.value = '';
    successMsg.value = '';
    rateLimited.value = false;
    const result = await documentStore.getEmailDefaults();
    if (result.success && result.data) {
      greeting.value = result.data.greeting || '';
      footer.value = result.data.footer || '';
      if (!subject.value && result.data.subject) {
        subject.value = result.data.subject;
      }
    }
  },
  { immediate: true },
);

function close() {
  emit('update:modelValue', false);
}

function addSection() {
  sections.value.push({ id: nextSectionId++, text: '' });
}

function removeSection(idx) {
  if (sections.value.length <= 1) return;
  sections.value.splice(idx, 1);
}

function moveSection(idx, delta) {
  const newIdx = idx + delta;
  if (newIdx < 0 || newIdx >= sections.value.length) return;
  const arr = sections.value;
  [arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]];
}

function removeAttachment(docId) {
  selectedDocIds.value = selectedDocIds.value.filter((id) => id !== docId);
}

function docTitle(docId) {
  if (props.document && docId === props.document.id) return props.document.title;
  const found = documentStore.documents.find((d) => d.id === docId);
  return found?.title || `documento-${docId}`;
}

async function send() {
  if (!canSend.value || isSending.value) return;
  isSending.value = true;
  errorMsg.value = '';
  successMsg.value = '';
  rateLimited.value = false;
  const payload = {
    recipient_email: recipient.value.trim(),
    subject: subject.value.trim(),
    greeting: greeting.value.trim(),
    footer: footer.value.trim(),
    sections: sections.value.map((s) => s.text).filter((t) => t.trim().length > 0),
    document_ids: selectedDocIds.value,
  };
  const result = await documentStore.sendDocumentEmail(payload);
  isSending.value = false;
  if (result.success) {
    successMsg.value = `Correo enviado a ${payload.recipient_email}.`;
    emit('sent');
    setTimeout(close, 1200);
  } else {
    rateLimited.value = result.code === 'rate_limited';
    errorMsg.value = result.errors?.error || 'No se pudo enviar el correo.';
  }
}
</script>
