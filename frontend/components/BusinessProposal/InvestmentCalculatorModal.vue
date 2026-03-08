<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')" />
        <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-5 border-b border-gray-100 bg-esmerald">
            <div>
              <h3 class="text-xl font-bold text-lemon">{{ t.title }}</h3>
              <p class="text-sm text-esmerald-light/70 mt-1">{{ t.subtitle }}</p>
            </div>
            <button
              class="w-8 h-8 rounded-lg flex items-center justify-center text-esmerald-light/60 hover:text-white hover:bg-white/10 transition-colors"
              @click="$emit('close')"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="overflow-y-auto px-6 py-6 flex-1">
            <div class="space-y-3">
              <div
                v-for="mod in localModules"
                :key="mod.id"
                class="flex items-center justify-between p-4 rounded-xl border transition-all"
                :class="[
                  mod.selected
                    ? 'bg-esmerald/5 border-esmerald/20'
                    : 'bg-gray-50 border-gray-200',
                  mod._locked ? 'opacity-80' : 'cursor-pointer hover:border-esmerald/40'
                ]"
                @click="toggleModule(mod)"
              >
                <div class="flex items-center gap-3">
                  <div
                    class="w-6 h-6 rounded-md border-2 flex items-center justify-center transition-colors"
                    :class="mod.selected
                      ? 'bg-esmerald border-esmerald text-white'
                      : 'border-gray-300 bg-white'"
                  >
                    <svg v-if="mod.selected" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <span class="font-medium" :class="mod.selected ? 'text-esmerald' : 'text-gray-500'">
                      {{ mod.name }}
                    </span>
                    <span v-if="mod._locked" class="ml-2 text-[10px] text-esmerald/50 font-medium uppercase">{{ t.required }}</span>
                    <div v-if="mod.groupTitle" class="text-[10px] text-gray-400 mt-0.5">{{ mod.groupTitle }}</div>
                  </div>
                </div>
                <span class="font-bold text-sm" :class="mod.selected ? 'text-esmerald' : 'text-gray-400'">
                  {{ mod.price ? formatPrice(mod.price) : t.included }}
                </span>
              </div>
            </div>
          </div>

          <!-- Footer with total -->
          <div class="px-6 py-5 border-t border-gray-100 bg-gray-50">
            <div class="flex items-center justify-between mb-4">
              <div>
                <span class="text-sm text-gray-500">{{ t.selectedModules }}</span>
                <span class="ml-1 text-sm font-medium text-esmerald">{{ selectedCount }}/{{ localModules.length }}</span>
              </div>
              <div class="text-right">
                <span class="text-sm text-gray-500 block">{{ t.estimatedTotal }}</span>
                <span class="text-2xl font-bold text-esmerald">{{ formatPrice(dynamicTotal) }}</span>
                <span class="text-xs text-gray-400 ml-1">{{ currency }}</span>
              </div>
            </div>
            <button
              class="w-full py-3 bg-esmerald text-lemon rounded-xl font-bold text-sm hover:bg-esmerald/90 transition-colors shadow-md"
              @click="confirmSelection"
            >
              {{ t.confirm }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  visible: { type: Boolean, default: false },
  modules: { type: Array, default: () => [] },
  currency: { type: String, default: 'COP' },
  proposalUuid: { type: String, default: '' },
  language: { type: String, default: 'es' },
  totalInvestment: { type: String, default: '' },
});

function parseInvestment(str) {
  if (!str) return 0;
  const cleaned = String(str).replace(/[^\d]/g, '');
  return parseInt(cleaned, 10) || 0;
}

const emit = defineEmits(['close', 'update:selection']);

const i18n = {
  es: {
    title: 'Personaliza tu inversión',
    subtitle: 'Selecciona los módulos que necesitas',
    selectedModules: 'Módulos seleccionados:',
    estimatedTotal: 'Total inversión',
    confirm: 'Confirmar selección',
    included: 'Incluido',
    required: 'obligatorio',
  },
  en: {
    title: 'Customize your investment',
    subtitle: 'Select the modules you need',
    selectedModules: 'Selected modules:',
    estimatedTotal: 'Total investment',
    confirm: 'Confirm selection',
    included: 'Included',
    required: 'required',
  },
};

const t = computed(() => i18n[props.language] || i18n.es);

const localModules = ref([]);

watch(() => props.visible, (val) => {
  if (val) {
    const storageKey = `proposal-${props.proposalUuid}-modules`;
    let saved = null;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) saved = JSON.parse(raw);
    } catch (_e) { /* ignore */ }

    localModules.value = props.modules.map(m => {
      const locked = m.is_required === true;
      return {
        ...m,
        selected: locked ? true : (saved ? saved.includes(m.id) : true),
        _locked: locked,
      };
    });
  }
}, { immediate: true });

const selectedCount = computed(() => localModules.value.filter(m => m.selected).length);

const baseTotalInvestment = computed(() => parseInvestment(props.totalInvestment));

const dynamicTotal = computed(() => {
  const deselectedSum = localModules.value
    .filter(m => !m.selected)
    .reduce((sum, m) => sum + (m.price || 0), 0);
  return baseTotalInvestment.value - deselectedSum;
});

function formatPrice(value) {
  if (!value && value !== 0) return '';
  return '$' + Number(value).toLocaleString('es-CO', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function toggleModule(mod) {
  if (mod._locked) return;
  mod.selected = !mod.selected;
}

function confirmSelection() {
  const selectedIds = localModules.value.filter(m => m.selected).map(m => m.id);
  const storageKey = `proposal-${props.proposalUuid}-modules`;
  try {
    localStorage.setItem(storageKey, JSON.stringify(selectedIds));
  } catch (_e) { /* ignore */ }
  emit('update:selection', { selectedIds, total: dynamicTotal.value });
  emit('close');
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
