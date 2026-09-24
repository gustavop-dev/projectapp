<template>
  <BaseActionButton
    action="copy"
    :label="`Copiar Markdown de ${title}`"
    tooltip="Copiar Markdown"
    :loading="loading"
    :disabled="loading || Boolean(disabledReason)"
    :disabled-reason="disabledReason || 'Espera mientras se obtiene el contenido del documento.'"
    :status-label="loading ? 'Copiando…' : feedback.feedbackFor().label"
    :status-tone="feedback.feedbackFor().tone"
    @click="copyDocument"
  />
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue';
import { get_request } from '~/stores/services/request_http';
import { useClipboardFeedback } from '~/composables/useClipboardFeedback';
import { usePanelNotify } from '~/composables/usePanelNotify';

const props = defineProps({
  endpoint: { type: String, required: true },
  title: { type: String, required: true },
  disabledReason: { type: String, default: '' },
});
const loading = ref(false);
const feedback = useClipboardFeedback();
const notify = usePanelNotify();
let controller = null;

function reset() {
  controller?.abort();
  controller = null;
  loading.value = false;
  feedback.clearAllFeedback();
}

async function copyDocument() {
  if (loading.value || props.disabledReason) return;
  feedback.clearAllFeedback();
  loading.value = true;
  const request = new AbortController();
  controller = request;
  try {
    const { data } = await get_request(props.endpoint, { signal: request.signal });
    if (request.signal.aborted) return;
    if (!data.markdown?.trim()) throw new Error('El documento no contiene texto para copiar.');
    const copied = await feedback.copyText({
      text: data.markdown,
      onError: () => notify.error('No se pudo copiar. Revisa el permiso del portapapeles y vuelve a intentarlo.'),
    });
    if (copied && data.warnings?.length) {
      notify.warning({ title: 'Contenido copiado con observaciones', detail: data.warnings.join(' ') });
    }
  } catch (error) {
    if (!request.signal.aborted) {
      notify.error(error.response?.data?.error || error.message || 'No se pudo obtener el documento. Vuelve a intentarlo.');
    }
  } finally {
    if (controller === request) {
      loading.value = false;
      controller = null;
    }
  }
}

watch(() => props.endpoint, reset);
onBeforeUnmount(reset);
</script>
