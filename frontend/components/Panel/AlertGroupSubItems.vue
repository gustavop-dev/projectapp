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

/**
 * La fila no contiene ningún control, así que es el enlace ENTERO y no sólo su
 * título: clic con rueda, ctrl+clic, «abrir en pestaña nueva» y copiar la
 * dirección funcionan en cualquier punto de ella.
 */
defineProps<{
  proposals: Proposal[]
  /** Dirección del editor de una propuesta, ya resuelta por la página. */
  hrefFor: (proposalId: number) => string
}>()
</script>

<template>
  <div class="ml-6 mt-1 space-y-1">
    <BaseRowLink
      v-for="proposal in proposals"
      :key="proposal.id"
      :to="hrefFor(proposal.id)"
      :data-testid="`alert-subitem-${proposal.id}`"
      class="flex items-center justify-between bg-surface-raised rounded-lg px-4 py-2 border border-border-muted transition-colors hover:border-border-default"
    >
      <span class="min-w-0">
        <span class="text-sm font-medium text-text-default">{{ proposal.title }}</span>
        <span v-for="(alert, idx) in proposal.alerts" :key="`${proposal.id}-${alert.alert_type}-${idx}`" class="block text-xs text-text-muted">
          {{ alert.icon }} {{ alert.message }}
        </span>
      </span>
      <svg class="w-4 h-4 text-text-subtle shrink-0 ml-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </BaseRowLink>
  </div>
</template>
