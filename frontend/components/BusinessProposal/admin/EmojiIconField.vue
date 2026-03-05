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
        type="button"
        class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-lg border border-gray-200 hover:bg-gray-50 text-sm cursor-pointer"
        @click.stop="showPicker = !showPicker"
      >😀</button>
    </div>
    <div v-if="showPicker" class="absolute z-50 top-full mt-1 right-0" @click.stop>
      <div class="fixed inset-0 z-40" @click="showPicker = false" />
      <div class="relative z-50">
        <EmojiPicker
          :native="true"
          :disable-skin-tones="true"
          @select="onSelectEmoji"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import EmojiPicker from 'vue3-emoji-picker';
import 'vue3-emoji-picker/css';

defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
});

const emit = defineEmits(['update:modelValue']);

const showPicker = ref(false);

function onSelectEmoji(emoji) {
  emit('update:modelValue', emoji.i);
  showPicker.value = false;
}
</script>
