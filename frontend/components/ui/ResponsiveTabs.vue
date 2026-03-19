<template>
  <div>
    <!-- Mobile: select dropdown (visible below md) -->
    <div class="md:hidden mb-6">
      <select
        :value="modelValue"
        class="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl text-sm font-medium
               text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800
               focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none
               appearance-none cursor-pointer"
        :style="selectArrowStyle"
        @change="$emit('update:modelValue', $event.target.value)"
      >
        <option
          v-for="tab in tabs"
          :key="tab.id"
          :value="tab.id"
        >
          {{ tab.label }}
        </option>
      </select>
    </div>

    <!-- Desktop: horizontal tab bar (visible at md+) -->
    <div class="hidden md:flex gap-1 mb-6 border-b border-gray-200 dark:border-gray-700">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px whitespace-nowrap"
        :class="modelValue === tab.id
          ? 'border-emerald-600 text-emerald-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'"
        @click="$emit('update:modelValue', tab.id)"
      >
        {{ tab.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Tab {
  id: string
  label: string
}

defineProps<{
  tabs: Tab[]
  modelValue: string
}>()

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const selectArrowStyle = "background-image: url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e\"); background-position: right 0.5rem center; background-repeat: no-repeat; background-size: 1.5em 1.5em; padding-right: 2.5rem;"
</script>
