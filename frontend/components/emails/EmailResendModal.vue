<template>
  <BaseModal
    :model-value="open"
    kind="form"
    @update:model-value="handleVisibility"
  >
    <form class="space-y-5 p-5 sm:p-6" data-testid="email-resend-modal" @submit.prevent="submit">
      <div>
        <h3 class="text-lg font-semibold text-text-default">Reenviar correo exacto</h3>
        <p class="mt-1 text-sm text-text-subtle">
          Sólo puedes cambiar el destinatario. El asunto, el cuerpo y los adjuntos
          saldrán desde la copia archivada.
        </p>
      </div>

      <BaseInput
        v-model="recipient"
        type="email"
        label="Destinatario"
        autocomplete="email"
        required
        data-testid="email-resend-recipient"
      />

      <div class="rounded-lg border border-border-muted bg-surface-muted p-3">
        <p class="text-[10px] font-medium uppercase tracking-wide text-text-subtle">Asunto bloqueado</p>
        <p class="mt-1 break-words text-sm text-text-default">{{ entry?.subject }}</p>
      </div>

      <div>
        <p class="text-[10px] font-medium uppercase tracking-wide text-text-subtle">
          Adjuntos archivados
        </p>
        <div v-if="entry?.attachments?.length" class="mt-2 space-y-2">
          <div
            v-for="attachment in entry.attachments"
            :key="attachment.id || attachment.filename"
            class="rounded-lg border border-border-muted px-3 py-2 text-sm text-text-default"
          >
            {{ attachment.filename }}
          </div>
        </div>
        <p v-else class="mt-1 text-sm text-text-subtle">Este correo no llevaba adjuntos.</p>
      </div>

      <BaseAlert v-if="errorMessage" variant="danger" title="No se pudo reenviar">
        {{ errorMessage }}
      </BaseAlert>

      <div class="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <BaseButton type="button" variant="ghost" :disabled="emailStore.isResending" @click="emit('close')">
          Cancelar
        </BaseButton>
        <BaseButton
          type="submit"
          :loading="emailStore.isResending"
          :disabled="!recipient.trim() || emailStore.isResending"
          data-testid="email-resend-confirm"
        >
          Reenviar sin cambios
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useEmailStore } from '~/stores/emails';

const props = defineProps({
  open: { type: Boolean, default: false },
  entry: { type: Object, default: null },
});
const emit = defineEmits(['close', 'resent']);
const emailStore = useEmailStore();
const recipient = ref('');
const errorMessage = ref('');

watch(
  () => [props.open, props.entry?.id],
  ([open]) => {
    if (!open) return;
    recipient.value = props.entry?.recipient || '';
    errorMessage.value = '';
  },
  { immediate: true },
);

function handleVisibility(value) {
  if (!value) emit('close');
}

async function submit() {
  if (!props.entry?.id || !recipient.value.trim()) return;
  errorMessage.value = '';
  const result = await emailStore.resendEmail(
    props.entry.id,
    recipient.value.trim(),
  );
  if (result.success) emit('resent', result.data);
  else errorMessage.value = result.message;
}
</script>
