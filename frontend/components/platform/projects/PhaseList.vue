<template>
  <div class="rounded-2xl border border-border-default bg-surface p-6">
    <div class="flex items-center justify-between">
      <h2 class="text-base font-medium text-text-default">Fases del proyecto</h2>
    </div>
    <p v-if="!phases.length" class="mt-4 text-sm text-green-light/60">
      Este proyecto no tiene fases vinculadas todavía.
    </p>
    <draggable
      v-else
      :model-value="phases"
      handle=".drag-handle"
      item-key="id"
      class="mt-4 space-y-2"
      @end="onReorderEnd"
    >
      <template #item="{ element }">
        <div class="flex items-center gap-3 rounded-xl border border-border-muted bg-surface-muted/30 px-4 py-3">
          <span class="drag-handle cursor-grab select-none text-green-light/40" aria-label="Arrastrar">⠿</span>
          <span class="font-medium text-text-default">{{ element.order }}. {{ element.proposal.title }}</span>
          <span class="ml-auto text-sm text-green-light/60">${{ element.proposal.total_amount }}</span>
          <button class="rounded-lg border border-border-default px-2 py-1 text-xs text-green-light" @click="onEditProposal(element.proposal.id)">Editar</button>
          <button
            :data-testid="`remove-phase-${element.id}`"
            class="rounded-lg border border-red-500/30 px-2 py-1 text-xs text-red-600"
            @click="onRemove(element.id)"
          >×</button>
        </div>
      </template>
    </draggable>
    <button
      class="mt-4 rounded-xl border border-dashed border-border-default px-3 py-2 text-sm text-text-default"
      @click="$emit('add-phase')"
    >+ Agregar fase desde propuesta del cliente</button>
  </div>
</template>

<script setup>
import draggable from 'vuedraggable'
import { usePlatformProjectsStore } from '~/stores/platform-projects'

const props = defineProps({
  projectId: { type: [String, Number], required: true },
  phases: { type: Array, required: true },
})
const emit = defineEmits(['add-phase', 'changed'])

const store = usePlatformProjectsStore()

async function onReorderEnd() {
  const items = props.phases.map((p, idx) => ({ id: p.id, order: idx + 1 }))
  const r = await store.reorderPhases(props.projectId, items)
  if (r.success) emit('changed')
}

async function onRemove(phaseId) {
  if (!window.confirm('¿Quitar esta fase del proyecto?')) return
  const r = await store.removePhase(props.projectId, phaseId)
  if (r.success) emit('changed')
}

function onEditProposal(proposalId) {
  window.open(`/panel/proposals/${proposalId}/edit`, '_blank')
}
</script>
