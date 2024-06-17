<template>
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-md">
      <div @click="hideModal" class="relative h-full w-full"></div>
      <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full h-full max-w-7xl max-h-[90vh] pt-4 px-8 bg-window-black bg-opacity-40 backdrop-blur-md rounded-xl">
        <div class="relative flex gap-2 left-0">
            <div @click="hideModal" class="w-3 h-3 bg-red-600 rounded-full cursor-pointer"></div>
            <div @click="hideModal" class="w-3 h-3 bg-yellow-600 rounded-full cursor-pointer"></div>
            <div @click="hideModal" class="w-3 h-3 bg-gray-600 rounded-full cursor-pointer"></div>
        </div>
        <Dune :spline="splineUrl" />
      </div>
    </div>
  </template>
  
  <script setup>
  import Dune from '@/components/spline/Backgrounds/Dune.vue';
  
  const props = defineProps({
    visible: Boolean,
    splineUrl: String
  });
  
  const emit = defineEmits(['update:visible']);
  
  const hideModal = () => {
    emit('update:visible', false);
  };
  </script>
  