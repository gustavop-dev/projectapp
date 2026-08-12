<template>
  <div class="lt-pwa" data-testid="linktree-pwa-block">
    <LinktreeIcon name="smartphone" :size="19" class="lt-pwa__icon" />
    <div class="lt-pwa__body">
      <div class="lt-pwa__copy">
        <span class="lt-pwa__title">{{ title }}</span>
        <span class="lt-pwa__description">{{ description }}</span>
      </div>
      <button type="button" class="lt-pwa__cta" @click="$emit('install')">
        Añadir a mi pantalla
      </button>
    </div>
  </div>
</template>

<script setup>
import LinktreeIcon from './LinktreeIcon.vue';

defineProps({
  title: { type: String, default: 'Guarda la tarjeta en tu teléfono' },
  description: {
    type: String,
    default: 'Queda como un ícono en tu pantalla de inicio, sin instalar nada de la tienda.',
  },
});
defineEmits(['install']);
</script>

<style scoped>
/* Square corners on purpose — the design keeps this block visually distinct
   from the pill buttons so it doesn't read as "one more link". */
.lt-pwa {
  display: flex;
  gap: 14px;
  padding: 16px;
  border: 1px solid rgba(240, 255, 61, 0.34);
  background: rgba(240, 255, 61, 0.06);
}
.lt-pwa__icon { color: #f0ff3d; flex: 0 0 auto; margin-top: 1px; }
.lt-pwa__body { display: flex; flex-direction: column; gap: 10px; }
.lt-pwa__copy { display: flex; flex-direction: column; gap: 3px; }
.lt-pwa__title { font-size: 13px; font-weight: 500; color: #ffffff; }
.lt-pwa__description { font-size: 12px; line-height: 17px; font-weight: 300; color: #809490; }
.lt-pwa__cta {
  align-self: flex-start;
  padding: 15px 20px;
  border: 1px solid #f0ff3d;
  border-radius: 999px;
  background: transparent;
  color: #f0ff3d;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 120ms ease-out;
}
.lt-pwa__cta:hover { background: rgba(240, 255, 61, 0.12); }
</style>
