<template>
  <div>
    <div class="mb-8">
      <NuxtLink to="/panel/proposals" class="text-sm text-gray-500 hover:text-gray-700 transition-colors">
        ← Volver a propuestas
      </NuxtLink>
      <div v-if="proposal" class="flex flex-wrap items-center gap-3 sm:gap-4 mt-2">
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
      <div class="flex gap-1 mb-6 border-b border-gray-200 overflow-hidden">
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
        <div class="bg-gray-50 rounded-xl p-4 sm:p-5 mb-6 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
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
          <div>
            <span class="text-gray-400 text-xs">Estado activo</span>
            <div class="flex items-center gap-2 mt-1">
              <button
                type="button"
                class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                :class="proposal.is_active ? 'bg-emerald-600' : 'bg-gray-200'"
                @click="handleToggleActive"
              >
                <span
                  class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                  :class="proposal.is_active ? 'translate-x-4' : 'translate-x-0'"
                />
              </button>
              <span class="text-xs" :class="proposal.is_active ? 'text-emerald-600' : 'text-gray-400'">
                {{ proposal.is_active ? 'Activa' : 'Inactiva' }}
              </span>
            </div>
          </div>
          <div>
            <span class="text-gray-400 text-xs">Automatizaciones</span>
            <div class="flex items-center gap-2 mt-1">
              <button
                type="button"
                class="relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none"
                :class="form.automations_paused ? 'bg-amber-500' : 'bg-emerald-600'"
                @click="toggleAutomationsPaused"
              >
                <span
                  class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                  :class="form.automations_paused ? 'translate-x-4' : 'translate-x-0'"
                />
              </button>
              <span class="text-xs" :class="form.automations_paused ? 'text-amber-600' : 'text-emerald-600'">
                {{ form.automations_paused ? '⏸ Pausadas' : 'Activas' }}
              </span>
            </div>
            <p class="text-[10px] text-gray-400 mt-1">Pausar emails automáticos (recordatorio, urgencia, inactividad).</p>
          </div>
        </div>

        <!-- Editable form -->
        <form class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-8 space-y-6" @submit.prevent="handleUpdate">
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
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Teléfono / WhatsApp</label>
            <input v-model="form.client_phone" type="tel" placeholder="+57 300 123 4567"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de proyecto</label>
              <select v-model="form.project_type"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white">
                <option value="">— Sin definir —</option>
                <option value="website">Sitio Web</option>
                <option value="ecommerce">E-commerce</option>
                <option value="webapp">Aplicación Web</option>
                <option value="landing">Landing Page</option>
                <option value="redesign">Rediseño</option>
                <option value="other">Otro</option>
              </select>
              <input
                v-if="form.project_type === 'other'"
                v-model="form.project_type_custom"
                type="text"
                placeholder="Especificar tipo de proyecto..."
                class="mt-2 w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de mercado</label>
              <select v-model="form.market_type"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white">
                <option value="">— Sin definir —</option>
                <option value="b2b">B2B</option>
                <option value="b2c">B2C</option>
                <option value="saas">SaaS</option>
                <option value="retail">Retail</option>
                <option value="services">Servicios profesionales</option>
                <option value="health">Salud</option>
                <option value="education">Educación</option>
                <option value="real_estate">Inmobiliaria</option>
                <option value="other">Otro</option>
              </select>
              <input
                v-if="form.market_type === 'other'"
                v-model="form.market_type_custom"
                type="text"
                placeholder="Especificar tipo de mercado..."
                class="mt-2 w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
            <select v-model="form.language"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white">
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
            <p class="text-xs text-gray-400 mt-1">Solo afecta los títulos por defecto al crear. Cambiar aquí no regenera las secciones existentes.</p>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Recordatorio (días después de enviar)</label>
              <input v-model.number="form.reminder_days" type="number" min="1" max="30"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
              <p class="text-xs text-gray-400 mt-1">Se enviará un email recordatorio al cliente X días después de enviar la propuesta.</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Urgencia (días después de enviar)</label>
              <input v-model.number="form.urgency_reminder_days" type="number" min="1" max="30"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
              <p class="text-xs text-gray-400 mt-1">Se enviará un email de urgencia X días después de enviar (incluye descuento si % > 0).</p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Descuento (%)</label>
            <input v-model.number="form.discount_percent" type="number" min="0" max="100"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
            <p class="text-xs text-gray-400 mt-1">0 = sin descuento en email de urgencia.</p>
          </div>

          <div v-if="updateMsg" class="text-sm px-4 py-3 rounded-xl" :class="updateMsg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'">
            {{ updateMsg.text }}
          </div>

          <div class="flex flex-wrap items-center gap-3 sm:gap-4 pt-2">
            <button type="submit" :disabled="proposalStore.isUpdating"
              class="px-5 sm:px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50">
              {{ proposalStore.isUpdating ? 'Guardando...' : 'Guardar Cambios' }}
            </button>
            <button
              v-if="proposal.status === 'draft' && proposal.client_email"
              type="button"
              class="px-5 sm:px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm"
              @click="handleSend"
            >
              Enviar al Cliente
            </button>
            <button
              v-else-if="['sent', 'viewed'].includes(proposal.status) && proposal.client_email"
              type="button"
              class="px-5 sm:px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm"
              @click="handleResend"
            >
              Re-enviar al Cliente
            </button>
            <a :href="'/proposal/' + proposal.uuid + '?preview=1'" target="_blank"
              class="text-sm text-gray-500 hover:text-emerald-600 transition-colors">
              Preview →
            </a>
          </div>
        </form>
      </div>

      <!-- Tab: Activity -->
      <div v-show="activeTab === 'activity'">
        <!-- Log activity form -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-6">
          <h3 class="text-sm font-semibold text-gray-700 mb-3">Registrar actividad</h3>
          <div class="flex flex-col sm:flex-row gap-3">
            <select v-model="activityForm.change_type" class="px-3 py-2 border border-gray-200 rounded-xl text-sm bg-white focus:ring-1 focus:ring-emerald-500 outline-none sm:w-40">
              <option value="call">📞 Llamada</option>
              <option value="meeting">🤝 Reunión</option>
              <option value="followup">📩 Seguimiento</option>
              <option value="note">📝 Nota</option>
            </select>
            <input v-model="activityForm.description" type="text" placeholder="Descripción de la actividad..." class="flex-1 px-3 py-2 border border-gray-200 rounded-xl text-sm focus:ring-1 focus:ring-emerald-500 outline-none" @keydown.enter.prevent="submitActivity" />
            <button type="button" :disabled="!activityForm.description.trim() || isSubmittingActivity" class="px-4 py-2 bg-emerald-600 text-white rounded-xl text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 whitespace-nowrap" @click="submitActivity">
              {{ isSubmittingActivity ? 'Guardando...' : 'Agregar' }}
            </button>
          </div>
        </div>

        <!-- Timeline -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 class="text-sm font-semibold text-gray-700 mb-4">Historial de actividad</h3>
          <div v-if="!changeLogs.length" class="text-center py-8 text-sm text-gray-400">Sin actividad registrada.</div>
          <div v-else class="relative pl-6 space-y-0">
            <div class="absolute left-[9px] top-2 bottom-2 w-px bg-gray-200" />
            <div v-for="log in changeLogs" :key="log.id" class="relative pb-5 last:pb-0">
              <div class="absolute -left-6 top-1 w-[18px] h-[18px] rounded-full border-2 border-white shadow-sm flex items-center justify-center text-[10px]" :class="activityDotClass(log.change_type)">
                {{ activityIcon(log.change_type) }}
              </div>
              <div class="ml-2">
                <div class="flex items-baseline gap-2">
                  <span class="text-xs font-semibold" :class="activityLabelClass(log.change_type)">{{ activityLabel(log.change_type) }}</span>
                  <span class="text-[10px] text-gray-400">{{ formatLogDate(log.created_at) }}</span>
                </div>
                <p class="text-sm text-gray-600 mt-0.5">{{ log.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab: Analytics -->
      <div v-show="activeTab === 'analytics'">
        <ProposalAnalytics :proposalId="proposal.id" :proposal="proposal" />
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
              class="px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-2 cursor-pointer hover:bg-gray-50 transition-colors"
              @click="toggleSection(section.id)"
            >
              <div class="flex items-center gap-4">
                <span class="text-xs text-gray-400 font-mono w-6">{{ section.order + 1 }}</span>
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
            <div v-if="expandedSections.has(section.id)" class="border-t border-gray-100 px-3 sm:px-6 py-4 sm:py-6">
              <SectionEditor
                :section="section"
                :proposalData="proposal"
                @save="handleSaveSection"
              />
            </div>
          </div>
        </div>

        <!-- Sticky send bar for sections tab -->
        <div v-if="proposal.client_email" class="sticky bottom-0 mt-4 bg-white/95 backdrop-blur-sm border border-gray-100 rounded-xl shadow-lg px-5 py-3 flex items-center justify-between gap-3 z-10">
          <div class="flex items-center gap-2 text-xs text-gray-500">
            <a :href="'/proposal/' + proposal.uuid + '?preview=1'" target="_blank" class="text-emerald-600 hover:underline">Preview →</a>
          </div>
          <div class="flex items-center gap-3">
            <button
              v-if="proposal.status === 'draft'"
              type="button"
              class="px-5 py-2 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm"
              @click="handleSend"
            >
              📤 Enviar al Cliente
            </button>
            <button
              v-else-if="['sent', 'viewed'].includes(proposal.status)"
              type="button"
              class="px-5 py-2 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm"
              @click="handleResend"
            >
              🔄 Re-enviar al Cliente
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- Pre-send checklist modal -->
    <Teleport to="body">
      <div v-if="showSendChecklist" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="showSendChecklist = false">
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-6 sm:p-8">
          <h3 class="text-lg font-bold text-gray-900 mb-1">Checklist pre-envío</h3>
          <p class="text-sm text-gray-500 mb-5">Verifica que todo esté listo antes de enviar.</p>
          <ul class="space-y-3 mb-6">
            <li v-for="(item, idx) in sendChecklist" :key="idx" class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                :class="item.pass ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-500'">
                {{ item.pass ? '✓' : '✗' }}
              </span>
              <span class="text-sm" :class="item.pass ? 'text-gray-700' : 'text-red-600 font-medium'">{{ item.label }}</span>
            </li>
          </ul>
          <div class="flex gap-3 justify-end">
            <button class="px-5 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showSendChecklist = false">
              Cancelar
            </button>
            <button
              class="px-5 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!allChecksPassing"
              @click="confirmSend"
            >
              Enviar al Cliente
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import SectionEditor from '~/components/BusinessProposal/admin/SectionEditor.vue';
import ProposalAnalytics from '~/components/BusinessProposal/admin/ProposalAnalytics.vue';

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
  { id: 'activity', label: 'Actividad' },
  { id: 'analytics', label: 'Analytics' },
];

const expandedSections = ref(new Set());
const updateMsg = ref(null);

const form = reactive({
  title: '',
  client_name: '',
  client_email: '',
  client_phone: '',
  project_type: '',
  market_type: '',
  project_type_custom: '',
  market_type_custom: '',
  language: 'es',
  total_investment: 0,
  currency: 'COP',
  expires_at: '',
  reminder_days: 10,
  urgency_reminder_days: 15,
  discount_percent: 0,
  automations_paused: false,
});

onMounted(async () => {
  const id = route.params.id;
  await proposalStore.fetchProposal(id);
  if (proposal.value) {
    Object.assign(form, {
      title: proposal.value.title,
      client_name: proposal.value.client_name,
      client_email: proposal.value.client_email || '',
      client_phone: proposal.value.client_phone || '',
      project_type: proposal.value.project_type || '',
      market_type: proposal.value.market_type || '',
      project_type_custom: proposal.value.project_type_custom || '',
      market_type_custom: proposal.value.market_type_custom || '',
      language: proposal.value.language || 'es',
      total_investment: Number(proposal.value.total_investment),
      currency: proposal.value.currency,
      expires_at: proposal.value.expires_at
        ? proposal.value.expires_at.slice(0, 16)
        : '',
      reminder_days: proposal.value.reminder_days,
      urgency_reminder_days: proposal.value.urgency_reminder_days ?? 15,
      discount_percent: proposal.value.discount_percent ?? 0,
      automations_paused: proposal.value.automations_paused ?? false,
    });
  }
});

async function toggleAutomationsPaused() {
  form.automations_paused = !form.automations_paused;
  const result = await proposalStore.updateProposal(proposal.value.id, {
    automations_paused: form.automations_paused,
  });
  if (result.success) {
    updateMsg.value = { type: 'success', text: form.automations_paused ? 'Automatizaciones pausadas.' : 'Automatizaciones reactivadas.' };
  } else {
    form.automations_paused = !form.automations_paused;
    updateMsg.value = { type: 'error', text: 'Error al cambiar automatizaciones.' };
  }
}

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

const showSendChecklist = ref(false);
const sendChecklist = computed(() => {
  const checks = [
    { label: 'Email del cliente configurado', pass: !!form.client_email?.trim() },
    { label: 'Nombre del cliente', pass: !!form.client_name?.trim() },
    { label: 'Inversión > $0', pass: Number(form.total_investment) > 0 },
    { label: 'Fecha de expiración futura', pass: !!form.expires_at && new Date(form.expires_at) > new Date() },
    { label: 'Al menos 1 sección habilitada', pass: allSections.value?.some(s => s.is_enabled) },
  ];
  return checks;
});
const allChecksPassing = computed(() => sendChecklist.value.every(c => c.pass));

function handleSend() {
  showSendChecklist.value = true;
}

async function confirmSend() {
  showSendChecklist.value = false;
  const result = await proposalStore.sendProposal(proposal.value.id);
  if (result.success) {
    updateMsg.value = { type: 'success', text: 'Propuesta enviada al cliente.' };
  } else {
    updateMsg.value = { type: 'error', text: result.errors?.error || 'Error al enviar.' };
  }
}

async function handleResend() {
  if (!confirm('¿Re-enviar esta propuesta? Se mantendrá la misma fecha de expiración.')) return;
  const result = await proposalStore.resendProposal(proposal.value.id);
  if (result.success) {
    updateMsg.value = { type: 'success', text: 'Propuesta re-enviada al cliente.' };
  } else {
    updateMsg.value = { type: 'error', text: result.errors?.error || 'Error al re-enviar.' };
  }
}

async function handleToggleActive() {
  const result = await proposalStore.toggleProposalActive(proposal.value.id);
  if (result.success) {
    const label = result.data.is_active ? 'activada' : 'desactivada';
    updateMsg.value = { type: 'success', text: `Propuesta ${label}.` };
  } else {
    updateMsg.value = { type: 'error', text: 'Error al cambiar el estado.' };
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

// --- Activity timeline ---
const activityForm = reactive({ change_type: 'note', description: '' });
const isSubmittingActivity = ref(false);
const changeLogs = computed(() => proposal.value?.change_logs || []);

async function submitActivity() {
  if (!activityForm.description.trim() || isSubmittingActivity.value) return;
  isSubmittingActivity.value = true;
  try {
    const result = await proposalStore.logActivity(proposal.value.id, {
      change_type: activityForm.change_type,
      description: activityForm.description.trim(),
    });
    if (result.success) {
      activityForm.description = '';
      await proposalStore.fetchProposal(proposal.value.id);
    }
  } finally {
    isSubmittingActivity.value = false;
  }
}

const activityMeta = {
  created: { icon: '✨', label: 'Creada', dot: 'bg-gray-200', text: 'text-gray-500' },
  updated: { icon: '✏️', label: 'Editada', dot: 'bg-gray-200', text: 'text-gray-500' },
  sent: { icon: '📤', label: 'Enviada', dot: 'bg-blue-100', text: 'text-blue-600' },
  viewed: { icon: '👁', label: 'Vista', dot: 'bg-green-100', text: 'text-green-600' },
  accepted: { icon: '✅', label: 'Aceptada', dot: 'bg-emerald-100', text: 'text-emerald-600' },
  rejected: { icon: '❌', label: 'Rechazada', dot: 'bg-red-100', text: 'text-red-600' },
  resent: { icon: '🔁', label: 'Re-enviada', dot: 'bg-blue-100', text: 'text-blue-600' },
  expired: { icon: '⏰', label: 'Expirada', dot: 'bg-yellow-100', text: 'text-yellow-600' },
  duplicated: { icon: '📋', label: 'Duplicada', dot: 'bg-gray-200', text: 'text-gray-500' },
  commented: { icon: '💬', label: 'Comentario', dot: 'bg-purple-100', text: 'text-purple-600' },
  reengagement: { icon: '🔔', label: 'Reengagement', dot: 'bg-orange-100', text: 'text-orange-600' },
  call: { icon: '📞', label: 'Llamada', dot: 'bg-sky-100', text: 'text-sky-600' },
  meeting: { icon: '🤝', label: 'Reunión', dot: 'bg-indigo-100', text: 'text-indigo-600' },
  followup: { icon: '📩', label: 'Seguimiento', dot: 'bg-amber-100', text: 'text-amber-600' },
  note: { icon: '📝', label: 'Nota', dot: 'bg-gray-200', text: 'text-gray-600' },
};
function activityIcon(type) { return activityMeta[type]?.icon || '•'; }
function activityLabel(type) { return activityMeta[type]?.label || type; }
function activityDotClass(type) { return activityMeta[type]?.dot || 'bg-gray-200'; }
function activityLabelClass(type) { return activityMeta[type]?.text || 'text-gray-500'; }

function formatLogDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
</script>
