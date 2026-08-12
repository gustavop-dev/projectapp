<template>
  <component
    :is="isInteractive ? 'button' : 'a'"
    :type="isInteractive ? 'button' : undefined"
    :href="isInteractive ? undefined : button.href || undefined"
    :target="isExternal ? '_blank' : undefined"
    :rel="isExternal ? 'noopener' : undefined"
    class="lt-btn"
    :class="[`lt-btn--${button.tier}`, { 'lt-btn--pending': button.is_pending }]"
    :data-testid="`linktree-button-${button.id ?? button.action}`"
    @click="onClick"
  >
    <LinktreeIcon :name="button.resolved_icon" :size="button.tier === 'primary' ? 18 : 17" />
    <span class="lt-btn__label">{{ button.label }}</span>
    <span v-if="button.is_pending" class="lt-btn__pending-tag">PENDIENTE</span>
    <LinktreeIcon
      v-else-if="button.tier === 'row'"
      name="arrow-up-right"
      :size="15"
      class="lt-btn__arrow"
    />
  </component>
</template>

<script setup>
import { computed } from 'vue';
import LinktreeIcon from './LinktreeIcon.vue';

const props = defineProps({
  button: { type: Object, required: true },
});
const emit = defineEmits(['action']);

// vcard / pwa-install buttons act in-page; url / mailto buttons navigate.
const isInteractive = computed(
  () => ['download-vcard', 'pwa-install'].includes(props.button.kind) || props.button.is_pending
);
const isExternal = computed(
  () => !isInteractive.value && /^https?:/i.test(props.button.href || '')
);

const onClick = (event) => {
  if (props.button.is_pending) {
    event.preventDefault();
    return;
  }
  if (isInteractive.value) emit('action', props.button);
};
</script>

<style scoped>
/* Fixed brand palette by design (Linktree.dc.html): esmerald #001713,
   lemon #F0FF3D, muted #809490 — deliberately NOT theme tokens. */
.lt-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-radius: 999px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  background: transparent;
  transition: background 120ms ease-out, border-color 120ms ease-out,
    color 120ms ease-out, transform 120ms ease-out;
}

.lt-btn--primary {
  padding: 17px 24px;
  background: #f0ff3d;
  border: none;
  color: #001713;
  font-size: 15px;
  font-weight: 700;
}
.lt-btn--primary:hover { background: #ffffff; }
.lt-btn--primary:active { transform: scale(0.97); }

.lt-btn--featured {
  padding: 16px 22px;
  border: 1px solid #f0ff3d;
  color: #f0ff3d;
  font-size: 15px;
}
.lt-btn--featured:hover { background: rgba(240, 255, 61, 0.12); }

.lt-btn--pair {
  flex: 1;
  padding: 16px 12px;
  gap: 8px;
  border: 1px solid #f0ff3d;
  color: #f0ff3d;
}
.lt-btn--pair:hover { background: rgba(240, 255, 61, 0.12); }

.lt-btn--row {
  justify-content: flex-start;
  gap: 12px;
  padding: 15px 22px;
  border: 1px solid rgba(128, 148, 144, 0.34);
  color: #ffffff;
}
.lt-btn--row:hover { border-color: #f0ff3d; color: #f0ff3d; }
.lt-btn--row .lt-btn__label { flex: 1; text-align: left; }
.lt-btn__arrow { color: #809490; flex: 0 0 auto; }

/* Unresolved destination: dashed gray, never lemon (design rule). */
.lt-btn--pending,
.lt-btn--pending:hover {
  background: transparent;
  border: 1px dashed rgba(128, 148, 144, 0.6);
  color: #809490;
  cursor: default;
  transform: none;
}
.lt-btn__pending-tag {
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 1.4px;
  color: #809490;
}
</style>
