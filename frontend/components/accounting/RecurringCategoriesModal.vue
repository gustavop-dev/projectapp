<script setup>
import { ref, watch } from 'vue'
import draggable from 'vuedraggable'

const props = defineProps({
  open: { type: Boolean, default: false },
  categories: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'create', 'rename', 'delete', 'reorder'])

const newName = ref('')
/** Mutable mirror: vuedraggable owns the array it reorders. */
const localCategories = ref([])

watch(
  () => props.categories,
  (categories) => {
    localCategories.value = categories.map((category) => ({ ...category }))
  },
  { immediate: true, deep: true },
)

watch(
  () => props.open,
  (open) => {
    if (open) newName.value = ''
  },
)

function onCreate() {
  const name = newName.value.trim()
  if (!name) return
  emit('create', name)
  newName.value = ''
}

function onRename(category, value) {
  const name = String(value).trim()
  if (!name || name === category.name) return
  emit('rename', { id: category.id, name })
}

function onDragEnd() {
  emit('reorder', localCategories.value.map((category) => category.id))
}
</script>

<template>
  <BaseModal
    :model-value="open"
    kind="form"
    size="md"
    title-id="recurring-categories-title"
    @close="emit('close')"
  >
    <div class="px-6 pt-6 pb-2">
      <h3 id="recurring-categories-title" class="text-lg font-bold text-text-default">
        Categorías de recurrentes
      </h3>
      <p class="text-sm text-text-subtle mt-1">
        Arrastra para cambiar el orden de los grupos en la tabla.
      </p>
    </div>

    <div class="px-6 py-4 space-y-4">
      <p
        v-if="localCategories.length === 0"
        class="text-sm text-text-subtle py-2"
      >
        Aún no hay categorías.
      </p>

      <draggable
        v-else
        v-model="localCategories"
        item-key="id"
        handle=".category-drag-handle"
        ghost-class="opacity-30"
        :disabled="saving"
        class="space-y-2"
        @end="onDragEnd"
      >
        <template #item="{ element: category }">
          <div
            class="flex items-center gap-2 bg-surface-raised rounded-lg px-3 py-2"
            :data-testid="`recurring-category-row-${category.id}`"
          >
            <span
              class="category-drag-handle cursor-grab select-none text-text-subtle"
              :data-testid="`recurring-category-drag-${category.id}`"
              title="Arrastra para reordenar"
            >⠿</span>
            <BaseInput
              :model-value="category.name"
              class="flex-1"
              :aria-label="`Nombre de ${category.name}`"
              :data-testid="`recurring-category-name-${category.id}`"
              @change="onRename(category, $event.target.value)"
            />
            <span class="text-xs text-text-subtle tabular-nums w-16 text-right">
              {{ category.payment_count }} pago{{ category.payment_count === 1 ? '' : 's' }}
            </span>
            <BaseActionButton
              action="delete"
              variant="danger-ghost"
              size="md"
              :label="`Eliminar ${category.name}`"
              :data-testid="`recurring-category-delete-${category.id}`"
              @click="emit('delete', category)"
            />
          </div>
        </template>
      </draggable>

      <form class="flex items-center gap-2 pt-2" @submit.prevent="onCreate">
        <BaseInput
          v-model="newName"
          placeholder="Nueva categoría..."
          class="flex-1"
          aria-label="Nombre de la nueva categoría"
          data-testid="recurring-category-new-name"
        />
        <BaseButton
          type="submit"
          variant="secondary"
          :disabled="saving || !newName.trim()"
          data-testid="recurring-category-create"
        >
          <BaseActionIcon action="create" />
          <span>Agregar</span>
        </BaseButton>
      </form>

      <div class="flex items-center justify-end pt-2">
        <BaseButton type="button" variant="primary" @click="emit('close')">
          Listo
        </BaseButton>
      </div>
    </div>
  </BaseModal>
</template>
