<template>
  <div>
    <div class="mb-8">
      <NuxtLink to="/panel/proposals" class="text-sm text-gray-500 hover:text-gray-700 transition-colors">
        ← Volver a propuestas
      </NuxtLink>
      <div v-if="proposal" class="flex items-center gap-4 mt-2">
        <h1 class="text-2xl font-light text-gray-900">{{ proposal.title }}</h1>
        <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusClass(proposal.status)">
          {{ proposal.status }}
        </span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="proposalStore.isLoading" class="text-center py-12 text-gray-400 text-sm">
      Cargando...
    </div>

    <template v-else-if="proposal">
      <!-- Tabs -->
      <div class="flex gap-1 mb-6 border-b border-gray-200">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px"
          :class="activeTab === tab.id
            ? 'border-emerald-600 text-emerald-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab: General -->
      <div v-show="activeTab === 'general'" class="max-w-2xl">
        <!-- Read-only info -->
        <div class="bg-gray-50 rounded-xl p-5 mb-6 grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-gray-400 text-xs">UUID</span>
            <p class="text-gray-700 font-mono text-xs mt-0.5">{{ proposal.uuid }}</p>
          </div>
          <div>
            <span class="text-gray-400 text-xs">URL pública</span>
            <p class="mt-0.5">
              <a :href="'/proposal/' + proposal.uuid" target="_blank" class="text-emerald-600 hover:underline text-xs break-all">
                /proposal/{{ proposal.uuid }}
              </a>
            </p>
          </div>
          <div>
            <span class="text-gray-400 text-xs">Vistas</span>
            <p class="text-gray-700 mt-0.5">{{ proposal.view_count }}</p>
          </div>
          <div>
            <span class="text-gray-400 text-xs">Enviada</span>
            <p class="text-gray-700 mt-0.5">
              {{ proposal.sent_at ? new Date(proposal.sent_at).toLocaleString() : '—' }}
            </p>
          </div>
        </div>

        <!-- Editable form -->
        <form class="bg-white rounded-xl shadow-sm border border-gray-100 p-8 space-y-6" @submit.prevent="handleUpdate">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Título</label>
            <input v-model="form.title" type="text" required
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre del cliente</label>
            <input v-model="form.client_name" type="text" required
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Email del cliente</label>
            <input v-model="form.client_email" type="email"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Inversión total</label>
              <input v-model.number="form.total_investment" type="number" min="0" step="0.01"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Moneda</label>
              <select v-model="form.currency"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white">
                <option value="COP">COP</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fecha de expiración</label>
            <input v-model="form.expires_at" type="datetime-local"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Días para recordatorio</label>
            <input v-model.number="form.reminder_days" type="number" min="1" max="30"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
          </div>

          <div v-if="updateMsg" class="text-sm px-4 py-3 rounded-xl" :class="updateMsg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'">
            {{ updateMsg.text }}
          </div>

          <div class="flex items-center gap-4 pt-2">
            <button type="submit" :disabled="proposalStore.isUpdating"
              class="px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50">
              {{ proposalStore.isUpdating ? 'Guardando...' : 'Guardar Cambios' }}
            </button>
            <button
              v-if="proposal.status === 'draft' && proposal.client_email"
              type="button"
              class="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm"
              @click="handleSend"
            >
              Enviar al Cliente
            </button>
            <a :href="proposal.public_url" target="_blank"
              class="text-sm text-gray-500 hover:text-emerald-600 transition-colors">
              Preview →
            </a>
          </div>
        </form>
      </div>

      <!-- Tab: Sections -->
      <div v-show="activeTab === 'sections'">
        <div class="space-y-3">
          <div
            v-for="section in allSections"
            :key="section.id"
            class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden"
          >
            <!-- Section header -->
            <div
              class="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 transition-colors"
              @click="toggleSection(section.id)"
            >
              <div class="flex items-center gap-4">
                <span class="text-xs text-gray-400 font-mono w-6">{{ String(section.order + 1).padStart(2, '0') }}</span>
                <span class="text-sm font-medium text-gray-900">{{ section.title }}</span>
                <span class="text-xs text-gray-400">({{ section.section_type }})</span>
              </div>
              <div class="flex items-center gap-3">
                <label class="flex items-center gap-2 text-xs" @click.stop>
                  <input
                    type="checkbox"
                    :checked="section.is_enabled"
                    class="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                    @change="toggleEnabled(section)"
                  />
                  <span class="text-gray-500">Visible</span>
                </label>
                <svg
                  class="w-4 h-4 text-gray-400 transition-transform"
                  :class="{ 'rotate-180': expandedSections.has(section.id) }"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            <!-- Section content editor (expanded) -->
            <div v-if="expandedSections.has(section.id)" class="border-t border-gray-100 px-6 py-6">
              <SectionEditor
                :section="section"
                @save="handleSaveSection"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import SectionEditor from '~/components/BusinessProposal/admin/SectionEditor.vue';

definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const proposalStore = useProposalStore();

const proposal = computed(() => proposalStore.currentProposal);
const allSections = computed(() =>
  [...(proposal.value?.sections || [])].sort((a, b) => a.order - b.order)
);

const activeTab = ref('general');
const tabs = [
  { id: 'general', label: 'General' },
  { id: 'sections', label: 'Secciones' },
];

const expandedSections = ref(new Set());
const updateMsg = ref(null);

const form = reactive({
  title: '',
  client_name: '',
  client_email: '',
  total_investment: 0,
  currency: 'COP',
  expires_at: '',
  reminder_days: 5,
});

onMounted(async () => {
  const id = route.params.id;
  await proposalStore.fetchProposal(id);
  if (proposal.value) {
    Object.assign(form, {
      title: proposal.value.title,
      client_name: proposal.value.client_name,
      client_email: proposal.value.client_email || '',
      total_investment: Number(proposal.value.total_investment),
      currency: proposal.value.currency,
      expires_at: proposal.value.expires_at
        ? proposal.value.expires_at.slice(0, 16)
        : '',
      reminder_days: proposal.value.reminder_days,
    });
  }
});

async function handleUpdate() {
  updateMsg.value = null;
  const payload = { ...form };
  if (payload.expires_at) {
    payload.expires_at = new Date(payload.expires_at).toISOString();
  } else {
    payload.expires_at = null;
  }
  const result = await proposalStore.updateProposal(proposal.value.id, payload);
  if (result.success) {
    updateMsg.value = { type: 'success', text: 'Propuesta actualizada.' };
  } else {
    const errors = result.errors;
    updateMsg.value = {
      type: 'error',
      text: errors
        ? Object.entries(errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
        : 'Error al actualizar.',
    };
  }
}

async function handleSend() {
  if (!confirm('¿Enviar esta propuesta al cliente? Se programará un recordatorio automático.')) return;
  const result = await proposalStore.sendProposal(proposal.value.id);
  if (result.success) {
    updateMsg.value = { type: 'success', text: 'Propuesta enviada al cliente.' };
  } else {
    updateMsg.value = { type: 'error', text: result.errors?.error || 'Error al enviar.' };
  }
}

function toggleSection(id) {
  if (expandedSections.value.has(id)) {
    expandedSections.value.delete(id);
  } else {
    expandedSections.value.add(id);
  }
  expandedSections.value = new Set(expandedSections.value);
}

async function toggleEnabled(section) {
  await proposalStore.updateSection(section.id, { is_enabled: !section.is_enabled });
}

async function handleSaveSection({ sectionId, payload }) {
  await proposalStore.updateSection(sectionId, payload);
}

function statusClass(status) {
  const map = {
    draft: 'bg-gray-100 text-gray-600',
    sent: 'bg-blue-50 text-blue-700',
    viewed: 'bg-green-50 text-green-700',
    accepted: 'bg-emerald-50 text-emerald-700',
    rejected: 'bg-red-50 text-red-700',
    expired: 'bg-yellow-50 text-yellow-700',
  };
  return map[status] || 'bg-gray-100 text-gray-600';
}
</script>
