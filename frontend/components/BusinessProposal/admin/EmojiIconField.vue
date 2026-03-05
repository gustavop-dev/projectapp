<template>
  <div class="relative">
    <label v-if="label" class="block text-xs text-gray-500 mb-0.5">{{ label }}</label>
    <div class="flex items-center gap-1">
      <input
        :value="modelValue"
        :placeholder="placeholder || '😀'"
        class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
        @input="$emit('update:modelValue', $event.target.value)"
      />
      <button
        ref="buttonRef"
        type="button"
        class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg border border-gray-200 hover:bg-gray-50 text-sm cursor-pointer"
        @click.stop="showPicker = !showPicker"
      >😀</button>
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

watch(showPicker, async (val) => {
  if (val && buttonRef.value) {
    await nextTick();
    const rect = buttonRef.value.getBoundingClientRect();
    pickerPos.value = {
      top: rect.bottom + 4,
      left: Math.max(8, rect.right - 352),
    };
  }
});

function onSelectEmoji(emoji) {
  emit('update:modelValue', emoji.i);
  showPicker.value = false;
}
</script>
