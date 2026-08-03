<template>
  <div
    v-if="moduleLinkOptions.length || itemLinkOptions.length"
    class="space-y-1 pt-1"
  >
    <button
      type="button"
      class="text-xs text-text-brand"
      :aria-expanded="open"
      data-testid="technical-req-links-toggle"
      @click="open = !open"
    >
      Vincular alcance/ítems ({{ selectionCount }})
    </button>
    <template v-if="open">
      <div v-if="moduleLinkOptions.length" class="space-y-1 pt-1" data-testid="technical-req-module-links">
        <p class="text-[10px] text-text-muted">Vincular a alcance comercial (vacío = alcance base, siempre visible):</p>
        <div class="flex flex-wrap gap-x-2 gap-y-1">
          <label
            v-for="opt in moduleLinkOptions"
            :key="'rql-' + opt.id"
            class="flex items-center gap-1 text-[11px] text-text-default cursor-pointer"
          >
            <input
              type="checkbox"
              :checked="selectedModuleIds.has(opt.id)"
              class="rounded border-input-border text-text-brand"
              @change="toggleLinkedId(req.linked_module_ids, opt.id)"
            >
            <span class="max-w-[10rem] truncate" :title="opt.label">{{ opt.label }}</span>
          </label>
        </div>
      </div>
      <div v-if="itemLinkOptions.length" class="space-y-1 pt-1" data-testid="technical-req-item-links">
        <p class="text-[10px] text-text-muted">Vincular a ítems comerciales (vistas/componentes/funcionalidades que implementa este requerimiento):</p>
        <div v-for="grp in itemLinkOptions" :key="'rqi-' + grp.groupId" class="space-y-0.5">
          <p class="text-[10px] font-medium text-text-subtle">{{ grp.groupLabel }}</p>
          <div class="flex flex-wrap gap-x-2 gap-y-1 pl-2">
            <label
              v-for="it in grp.items"
              :key="'rqi-' + grp.groupId + '-' + it.id"
              class="flex items-center gap-1 text-[11px] text-text-default cursor-pointer"
            >
              <input
                type="checkbox"
                :checked="selectedItemIds.has(it.id)"
                class="rounded border-input-border text-text-brand"
                @change="toggleLinkedId(req.linked_item_ids, it.id)"
              >
              <span class="max-w-[12rem] truncate" :title="it.label">{{ it.label }}</span>
            </label>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  /** Reactive requirement slice of the editor's doc; its arrays are mutated in place. */
  req: { type: Object, required: true },
  /** { id, label }[] from proposal FR + investment modules */
  moduleLinkOptions: { type: Array, default: () => [] },
  /** { groupId, groupLabel, items: { id, label }[] }[] from FR items */
  itemLinkOptions: { type: Array, default: () => [] },
  /** The editor's expand-all (tests) renders the grids without a click. */
  forceOpen: { type: Boolean, default: false },
});

const open = ref(props.forceOpen);

// Set-backed lookups derived from the SAME arrays the toggles mutate:
// splice/push invalidates the computed so checkbox state stays correct, while
// serialization keeps reading the untouched arrays out of the editor's doc.
const selectedModuleIds = computed(() => new Set(props.req.linked_module_ids));
const selectedItemIds = computed(() => new Set(props.req.linked_item_ids));
const selectionCount = computed(
  () => (props.req.linked_module_ids?.length || 0) + (props.req.linked_item_ids?.length || 0),
);

function toggleLinkedId(arr, id) {
  const i = arr.indexOf(id);
  if (i >= 0) arr.splice(i, 1);
  else arr.push(id);
}
</script>
