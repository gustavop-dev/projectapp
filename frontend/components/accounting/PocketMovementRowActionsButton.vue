<script setup>
defineProps({
  row: { type: Object, required: true },
})

const emit = defineEmits(['open'])
</script>

<template>
  <div class="flex items-center justify-center">
    <BaseActionButton
      action="more"
      variant="ghost"
      size="sm"
      class="h-11 w-11 shrink-0"
      :label="`Acciones de ${row.concept || `movimiento ${row.id}`}`"
      :data-testid="`pocket-actions-${row.id}`"
      @click.stop="emit('open', row)"
    />
  </div>
</template>
