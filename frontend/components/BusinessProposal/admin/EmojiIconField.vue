<template>
  <div class="relative">
    <label v-if="label" class="block text-xs text-text-muted mb-0.5">{{ label }}</label>
    <div class="flex items-center gap-1">
      <input
        :value="modelValue"
        :placeholder="placeholder || '😀'"
        class="bg-input-bg w-full px-3 py-2 border border-border-default rounded-lg text-sm focus:ring-1 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
        @input="$emit('update:modelValue', $event.target.value)"
      />
      <BaseTooltip
        text="Seleccionar emoji"
        position="top"
        width="max-w-xs"
        min-width="min-w-0"
        :toggle-on-click="false"
      >
        <template #trigger="{ tooltipId }">
          <!-- panel-action-icons: allow-content-glyph — the button previews the emoji value being edited. -->
          <BaseButton
            :ref="setButtonRef"
            unstyled
            icon-only
            type="button"
            class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg border border-border-default hover:bg-surface-muted text-sm cursor-pointer"
            aria-label="Seleccionar emoji"
            :aria-describedby="tooltipId"
            @click.stop="showPicker = !showPicker"
          >😀</BaseButton>
        </template>
      </BaseTooltip>
    </div>
    <teleport to="body">
      <div v-if="showPicker" class="fixed inset-0 z-[9998]" @click="showPicker = false" />
      <div v-if="showPicker" ref="pickerRef" class="fixed z-[9999]" :style="pickerStyle" @click.stop>
        <EmojiPicker
          :native="true"
          :disable-skin-tones="true"
          @select="onSelectEmoji"
        />
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue';
import EmojiPicker from 'vue3-emoji-picker';
import 'vue3-emoji-picker/css';

defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
});

const emit = defineEmits(['update:modelValue']);

const showPicker = ref(false);
const buttonRef = ref(null);
const pickerPos = ref({ top: 0, left: 0 });

const pickerStyle = computed(() => ({
  top: `${pickerPos.value.top}px`,
  left: `${pickerPos.value.left}px`,
}));

function setButtonRef(component) {
  buttonRef.value = component?.$el || null;
}

watch(showPicker, async (val) => {
  if (val && buttonRef.value) {
    await nextTick();
    const rect = buttonRef.value.getBoundingClientRect();
    const pickerW = 352;
    const vw = window.innerWidth;
    let left = rect.left;
    if (left + pickerW > vw - 8) left = vw - pickerW - 8;
    if (left < 8) left = 8;
    pickerPos.value = {
      top: rect.bottom + 4,
      left,
    };
  }
});

function onSelectEmoji(emoji) {
  emit('update:modelValue', emoji.i);
  showPicker.value = false;
}
</script>
