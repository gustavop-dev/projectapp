<template>
  <div class="w-full mx-auto max-w-screen-2xl">
    <div :class="['grid grid-cols-1 min-w-0 gap-6', splitClass]">
      <div class="min-w-0">
        <slot name="main" />
      </div>
      <div class="min-w-0">
        <slot name="aside" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  ratio: {
    type: String,
    default: '1:1',
    validator: (value) => ['1:1', '3:2', '2:3', '5:4'].includes(value),
  },
});

const SPLIT_CLASSES = {
  '1:1': 'xl:grid-cols-2',
  '3:2': 'xl:grid-cols-[3fr_2fr]',
  '2:3': 'xl:grid-cols-[2fr_3fr]',
  '5:4': 'xl:grid-cols-[5fr_4fr]',
};

const splitClass = computed(() => SPLIT_CLASSES[props.ratio]);
</script>
