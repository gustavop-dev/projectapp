<script setup lang="ts">
type AlertItem = {
  alert_type: string
  message: string
  icon: string
}

type Proposal = {
  id: number
  title: string
  alerts: AlertItem[]
}

defineProps<{
  proposals: Proposal[]
}>()

const emit = defineEmits<{
  select: [proposalId: number, event: MouseEvent]
}>()
</script>

<template>
  <div class="ml-6 mt-1 space-y-1">
    <div
      v-for="proposal in proposals"
      :key="proposal.id"
      class="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-2 border border-gray-100 cursor-pointer transition-colors hover:border-gray-300 dark:bg-gray-700/50 dark:border-gray-600 dark:hover:border-gray-500"
      @click="emit('select', proposal.id, $event)"
    >
      <div class="min-w-0">
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ proposal.title }}</span>
        <div v-for="(alert, idx) in proposal.alerts" :key="`${proposal.id}-${alert.alert_type}-${idx}`" class="text-xs text-gray-500 dark:text-gray-400">
          {{ alert.icon }} {{ alert.message }}
        </div>
      </div>
      <svg class="w-4 h-4 text-gray-400 shrink-0 ml-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </div>
  </div>
</template>
