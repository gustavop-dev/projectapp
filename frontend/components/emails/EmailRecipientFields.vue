<template>
  <div class="space-y-3" :data-testid="`${testIdPrefix}-recipients`">
    <EmailRecipientPicker
      :model-value="toRecipients"
      label="Para"
      required
      :excluded-emails="recipientEmails(ccRecipients)"
      :total-count="totalCount"
      :max-total="maxTotal"
      :test-id="`${testIdPrefix}-to`"
      @update:model-value="emit('update:toRecipients', $event)"
    />

    <BaseButton
      v-if="!showCc"
      type="button"
      variant="ghost"
      size="sm"
      :data-testid="`${testIdPrefix}-show-cc`"
      @click="showCc = true"
    >
      Agregar CC
    </BaseButton>

    <EmailRecipientPicker
      v-else
      :model-value="ccRecipients"
      label="CC"
      :excluded-emails="recipientEmails(toRecipients)"
      :total-count="totalCount"
      :max-total="maxTotal"
      :test-id="`${testIdPrefix}-cc`"
      @update:model-value="emit('update:ccRecipients', $event)"
    />

    <p class="text-right text-[11px] text-text-subtle" :data-testid="`${testIdPrefix}-recipient-count`">
      {{ totalCount }}/{{ maxTotal }} destinatarios entre Para y CC
    </p>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import EmailRecipientPicker from '~/components/emails/EmailRecipientPicker.vue';
import { EMAIL_RECIPIENT_LIMIT, recipientEmails } from '~/utils/emailRecipients';

const props = defineProps({
  toRecipients: { type: Array, default: () => [] },
  ccRecipients: { type: Array, default: () => [] },
  maxTotal: { type: Number, default: EMAIL_RECIPIENT_LIMIT },
  testIdPrefix: { type: String, required: true },
});

const emit = defineEmits(['update:toRecipients', 'update:ccRecipients']);
const showCc = ref(Boolean(props.ccRecipients.length));
const totalCount = computed(() => props.toRecipients.length + props.ccRecipients.length);

watch(
  () => props.ccRecipients.length,
  (count) => {
    if (count) showCc.value = true;
  },
);
</script>
