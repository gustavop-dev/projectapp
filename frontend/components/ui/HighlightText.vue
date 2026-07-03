<script setup>
import { computed } from 'vue';
import { highlightSegments } from '~/utils/highlightSegments';

const props = defineProps({
  text: { type: [String, Number], default: '' },
  query: { type: String, default: '' },
});

const segments = computed(() => highlightSegments(props.text, props.query));
</script>

<template>
  <span>
    <template v-for="(segment, index) in segments" :key="index">
      <mark
        v-if="segment.hit"
        class="bg-warning-soft text-inherit rounded-sm px-0.5"
      >{{ segment.text }}</mark>
      <template v-else>{{ segment.text }}</template>
    </template>
  </span>
</template>
