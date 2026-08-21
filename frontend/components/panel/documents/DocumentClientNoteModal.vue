<template>
  <BaseModal
    :model-value="modelValue"
    size="lg"
    initial-focus="#document-client-note-subject"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <form class="p-6 space-y-5" data-testid="document-client-note-modal" @submit.prevent="apply">
      <div>
        <h3 class="text-base font-semibold text-text-default">Nota para el cliente</h3>
        <p class="text-xs text-text-muted mt-1">
          Guarda juntos los textos listos para enviar. Esta nota es privada y no aparece en el PDF ni en el portal del cliente.
        </p>
      </div>

      <div class="space-y-1.5">
        <div class="flex items-center justify-between gap-3">
          <label for="document-client-note-subject" class="text-sm font-medium text-text-default">
            Asunto del correo
          </label>
          <BaseButton
            type="button"
            variant="ghost"
            size="sm"
            :disabled="!draft.subject.trim()"
            data-testid="client-note-copy-subject"
            @click="copyText('subject', draft.subject)"
          >
            {{ copiedField === 'subject' ? 'Copiado' : 'Copiar asunto' }}
          </BaseButton>
        </div>
        <BaseInput
          id="document-client-note-subject"
          v-model="draft.subject"
          :disabled="readonly"
          maxlength="255"
          placeholder="Asunto breve y concreto"
          data-testid="client-note-subject"
        />
      </div>

      <div class="space-y-1.5">
        <div class="flex items-center justify-between gap-3">
          <label for="document-client-note-email" class="text-sm font-medium text-text-default">
            Correo
          </label>
          <BaseButton
            type="button"
            variant="ghost"
            size="sm"
            :disabled="!draft.emailBody.trim()"
            data-testid="client-note-copy-email"
            @click="copyText('email', draft.emailBody)"
          >
            {{ copiedField === 'email' ? 'Copiado' : 'Copiar correo' }}
          </BaseButton>
        </div>
        <BaseTextarea
          id="document-client-note-email"
          v-model="draft.emailBody"
          :disabled="readonly"
          rows="9"
          placeholder="Saludo, contenido y cierre del correo..."
          data-testid="client-note-email"
        />
      </div>

      <div class="space-y-1.5">
        <div class="flex items-center justify-between gap-3">
          <label for="document-client-note-whatsapp" class="text-sm font-medium text-text-default">
            WhatsApp
          </label>
          <BaseButton
            type="button"
            variant="ghost"
            size="sm"
            :disabled="!draft.whatsappMessage.trim()"
            data-testid="client-note-copy-whatsapp"
            @click="copyText('whatsapp', draft.whatsappMessage)"
          >
            {{ copiedField === 'whatsapp' ? 'Copiado' : 'Copiar WhatsApp' }}
          </BaseButton>
        </div>
        <BaseTextarea
          id="document-client-note-whatsapp"
          v-model="draft.whatsappMessage"
          :disabled="readonly"
          rows="5"
          placeholder="Mensaje breve que invita a revisar el correo..."
          data-testid="client-note-whatsapp"
        />
      </div>

      <div class="flex justify-end gap-2 pt-1">
        <BaseButton type="button" variant="ghost" data-testid="client-note-cancel" @click="close">
          {{ readonly ? 'Cerrar' : 'Cancelar' }}
        </BaseButton>
        <BaseButton
          v-if="!readonly"
          type="submit"
          variant="primary"
          data-testid="client-note-apply"
        >
          Aplicar al documento
        </BaseButton>
      </div>
    </form>
  </BaseModal>
</template>

<script setup>
import { reactive, ref, watch } from 'vue';
import { usePanelNotify } from '~/composables/usePanelNotify';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  subject: { type: String, default: '' },
  emailBody: { type: String, default: '' },
  whatsappMessage: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue', 'apply']);
const notify = usePanelNotify();
const copiedField = ref('');
const draft = reactive({ subject: '', emailBody: '', whatsappMessage: '' });

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return;
    draft.subject = props.subject;
    draft.emailBody = props.emailBody;
    draft.whatsappMessage = props.whatsappMessage;
    copiedField.value = '';
  },
  { immediate: true },
);

function close() {
  emit('update:modelValue', false);
}

function apply() {
  emit('apply', {
    subject: draft.subject.trim(),
    emailBody: draft.emailBody.trim(),
    whatsappMessage: draft.whatsappMessage.trim(),
  });
  close();
}

async function copyText(field, value) {
  try {
    await navigator.clipboard.writeText(value);
    copiedField.value = field;
  } catch {
    notify.error({
      title: 'No se pudo copiar al portapapeles',
      detail: 'Tu navegador bloqueó el acceso al portapapeles.',
    });
  }
}
</script>
