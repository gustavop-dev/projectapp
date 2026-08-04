<template>
  <BaseModal v-model="open" size="md">
    <div data-testid="qr-download-modal">
      <h3 class="text-lg font-bold text-text-default mb-4">Descargar QR — {{ card?.name }}</h3>

      <div class="flex justify-center mb-4">
        <canvas ref="canvasRef" data-testid="qr-canvas" />
      </div>

      <div class="space-y-3 mb-4">
        <BaseFormField label="Color del QR" for="qr-color">
          <input
            id="qr-color"
            v-model="foregroundColor"
            type="color"
            data-testid="qr-foreground-color"
            class="h-10 w-16 rounded-md border border-input-border bg-input-bg cursor-pointer"
          />
        </BaseFormField>

        <BaseFormField label="Color de fondo" for="qr-bg-color">
          <input
            id="qr-bg-color"
            v-model="backgroundColor"
            type="color"
            :disabled="transparentBackground"
            data-testid="qr-background-color"
            class="h-10 w-16 rounded-md border border-input-border bg-input-bg cursor-pointer disabled:opacity-50"
          />
        </BaseFormField>

        <BaseCheckbox v-model="transparentBackground" data-testid="qr-transparent-toggle">
          Fondo transparente
        </BaseCheckbox>
      </div>

      <div class="flex items-center justify-end gap-2">
        <BaseButton variant="ghost" size="sm" @click="open = false">Cerrar</BaseButton>
        <BaseButton variant="primary" size="sm" data-testid="qr-download-button" @click="download">
          Descargar PNG
        </BaseButton>
      </div>
    </div>
  </BaseModal>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue';
import QRCode from 'qrcode';
import BaseModal from '~/components/base/BaseModal.vue';
import BaseFormField from '~/components/base/BaseFormField.vue';
import BaseButton from '~/components/base/BaseButton.vue';
import BaseCheckbox from '~/components/base/BaseCheckbox.vue';

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  card: { type: Object, default: null },
});
const emit = defineEmits(['update:modelValue']);

const open = ref(props.modelValue);
watch(() => props.modelValue, (value) => { open.value = value; });
watch(open, (value) => emit('update:modelValue', value));

const canvasRef = ref(null);
const foregroundColor = ref('#000000');
const backgroundColor = ref('#ffffff');
const transparentBackground = ref(false);

function shortLinkFor(card) {
  return `${window.location.origin}/t/${card.id}/`;
}

async function renderQr() {
  if (!open.value || !props.card || !canvasRef.value) return;
  const lightColor = transparentBackground.value
    ? `${backgroundColor.value}00`
    : `${backgroundColor.value}ff`;
  await QRCode.toCanvas(canvasRef.value, shortLinkFor(props.card), {
    width: 240,
    margin: 2,
    color: {
      dark: `${foregroundColor.value}ff`,
      light: lightColor,
    },
  });
}

watch(
  [open, foregroundColor, backgroundColor, transparentBackground, () => props.card],
  async () => {
    await nextTick();
    await renderQr();
  },
);

onMounted(async () => {
  await nextTick();
  await renderQr();
});

function download() {
  if (!canvasRef.value || !props.card) return;
  const link = document.createElement('a');
  link.download = `qr-${props.card.name.replace(/\s+/g, '-').toLowerCase()}.png`;
  link.href = canvasRef.value.toDataURL('image/png');
  link.click();
}
</script>
