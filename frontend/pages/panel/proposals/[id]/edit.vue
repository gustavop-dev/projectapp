<template>
  <div>
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      @confirm="handleConfirmed"
      @cancel="handleCancelled"
    />
    <div class="mb-8">
      <NuxtLink :to="localePath('/panel/proposals')" class="text-sm text-gray-500 hover:text-gray-700 transition-colors">
        ← Volver a propuestas
      </NuxtLink>
      <div v-if="proposal" class="flex flex-wrap items-center gap-3 sm:gap-4 mt-2">
        <h1 class="text-2xl font-light text-gray-900 dark:text-gray-100">{{ proposal.title }}</h1>
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
      <ResponsiveTabs v-model="activeTab" :tabs="tabs" />

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
            <label class="block text-sm font-medium text-gray-700 mb-1">Hosting (% de inversión total)</label>
            <div class="flex items-center gap-3">
              <input v-model.number="form.hosting_percent" type="number" min="0" max="100"
                class="w-32 px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
              <span class="text-sm text-gray-500">%</span>
            </div>
            <div v-if="form.hosting_percent > 0 && form.total_investment > 0" class="mt-3 bg-blue-50 border border-blue-200 rounded-xl overflow-hidden">
              <div class="grid grid-cols-[1fr_auto] gap-x-4 text-sm divide-y divide-blue-100">
                <div class="px-4 py-2 text-blue-700 font-medium">Mensual</div>
                <div class="px-4 py-2 text-blue-800 font-semibold text-right">
                  ${{ Math.round(form.total_investment * form.hosting_percent / 100 / 12).toLocaleString() }} {{ form.currency }}
                </div>
                <div class="px-4 py-2 text-blue-700 font-medium">Trimestral</div>
                <div class="px-4 py-2 text-blue-800 font-semibold text-right">
                  ${{ Math.round(form.total_investment * form.hosting_percent / 100 / 12 * 3).toLocaleString() }} {{ form.currency }}
                </div>
                <template v-if="form.hosting_discount_quarterly">
                  <div class="px-4 py-2 text-blue-700 font-medium">
                    Trimestral
                    <span class="ml-1 text-xs text-emerald-600 font-normal">({{ form.hosting_discount_quarterly }}% dcto)</span>
                  </div>
                  <div class="px-4 py-2 text-emerald-700 font-semibold text-right">
                    ${{ Math.round(Math.round(form.total_investment * form.hosting_percent / 100 / 12) * (100 - form.hosting_discount_quarterly) / 100 * 3).toLocaleString() }} {{ form.currency }}
                  </div>
                </template>
                <div class="px-4 py-2 text-blue-700 font-medium">Semestral</div>
                <div class="px-4 py-2 text-blue-800 font-semibold text-right">
                  ${{ Math.round(form.total_investment * form.hosting_percent / 100 / 12 * 6).toLocaleString() }} {{ form.currency }}
                </div>
                <template v-if="form.hosting_discount_semiannual">
                  <div class="px-4 py-2 text-blue-700 font-medium">
                    Semestral
                    <span class="ml-1 text-xs text-emerald-600 font-normal">({{ form.hosting_discount_semiannual }}% dcto)</span>
                  </div>
                  <div class="px-4 py-2 text-emerald-700 font-semibold text-right">
                    ${{ Math.round(Math.round(form.total_investment * form.hosting_percent / 100 / 12) * (100 - form.hosting_discount_semiannual) / 100 * 6).toLocaleString() }} {{ form.currency }}
                  </div>
                </template>
                <div class="px-4 py-2 text-blue-700 font-medium">☁️ Anual</div>
                <div class="px-4 py-2 text-blue-800 font-semibold text-right">
                  ${{ Math.round(form.total_investment * form.hosting_percent / 100).toLocaleString() }} {{ form.currency }}
                </div>
              </div>
            </div>
            <p class="text-xs text-gray-400 mt-1">Se sincroniza con el % del Plan de Hosting en la sección "Tu inversión y cómo pagar".</p>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Dcto. semestral (%)</label>
              <input v-model.number="form.hosting_discount_semiannual" type="number" min="0" max="100"
                class="w-32 px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Dcto. trimestral (%)</label>
              <input v-model.number="form.hosting_discount_quarterly" type="number" min="0" max="100"
                class="w-32 px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none" />
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

      <!-- Tab: Prompt Proposal -->
      <div v-show="activeTab === 'prompt'" class="max-w-4xl">
        <p class="text-sm text-gray-500 mb-6">
          Este prompt se usa con IA (ChatGPT, Claude, etc.) para generar propuestas comerciales personalizadas a partir del JSON plantilla.
        </p>

        <!-- Action bar -->
        <div class="flex flex-wrap items-center gap-2 mb-4">
          <template v-if="!promptIsEditing">
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
              @click="startEditPrompt"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
              Editar
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
              @click="handleCopyPrompt"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              {{ promptCopied ? '¡Copiado!' : 'Copiar' }}
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
              @click="promptDownload"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              Descargar .md
            </button>
            <button
              v-if="promptText !== promptDefault"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-white border border-gray-200 rounded-xl hover:bg-red-50 transition-colors"
              @click="handleResetPrompt"
            >
              Restaurar original
            </button>
          </template>
          <template v-else>
            <button
              type="button"
              class="px-5 py-2 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors shadow-sm"
              @click="saveEditPrompt"
            >
              Guardar cambios
            </button>
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
              @click="cancelEditPrompt"
            >
              Cancelar
            </button>
          </template>
        </div>

        <!-- Editing mode -->
        <div v-if="promptIsEditing" class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <textarea
            v-model="promptEditBuffer"
            rows="30"
            class="w-full px-4 sm:px-6 py-4 text-xs font-mono leading-relaxed text-gray-800 bg-transparent border-0 outline-none resize-y focus:ring-0"
          ></textarea>
        </div>

        <!-- Read-only mode -->
        <div v-else class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="px-4 sm:px-6 py-4 max-h-[70vh] overflow-y-auto">
            <pre class="text-xs leading-relaxed text-gray-700 whitespace-pre-wrap font-mono break-words">{{ promptText }}</pre>
          </div>
        </div>

        <p v-if="promptText !== promptDefault" class="text-xs text-amber-600 mt-3">
          Este prompt ha sido personalizado. Usa "Restaurar original" para volver al valor por defecto.
        </p>
      </div>

      <!-- Tab: JSON -->
      <div v-show="activeTab === 'json'" class="max-w-4xl">
        <!-- Current JSON (read-only) -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6 mb-6">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <h3 class="text-sm font-medium text-gray-900">JSON de la propuesta</h3>
              <p class="text-xs text-gray-400 mt-0.5">Representación JSON completa — se actualiza al guardar cambios en otras pestañas.</p>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                :disabled="jsonExportLoading"
                @click="refreshExportJson"
              >
                <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': jsonExportLoading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Actualizar
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                @click="copyExportJson"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                {{ jsonCopied ? '¡Copiado!' : 'Copiar' }}
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                @click="downloadExportJson"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                Descargar
              </button>
            </div>
          </div>

          <div v-if="jsonExportLoading" class="text-center py-8 text-gray-400 text-sm">
            Cargando JSON...
          </div>
          <textarea
            v-else
            :value="exportJsonString"
            readonly
            rows="18"
            class="w-full px-4 py-3 border border-gray-200 rounded-xl text-xs font-mono leading-relaxed
                   bg-gray-50 text-gray-700 outline-none resize-y cursor-text select-all"
          />
        </div>

        <!-- Import JSON -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
          <h3 class="text-sm font-medium text-gray-900 mb-1">Importar JSON</h3>
          <p class="text-xs text-gray-400 mb-4">Pega o sube un JSON para reemplazar el contenido de la propuesta (metadata + secciones).</p>

          <div class="flex items-center gap-3 mb-3">
            <label
              class="inline-flex items-center gap-2 px-3 py-1.5 border border-gray-200 rounded-lg text-xs
                     text-gray-700 hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              Subir .json
              <input type="file" accept=".json" class="hidden" @change="handleJsonFileUpload" />
            </label>
            <span v-if="jsonImportFileName" class="text-xs text-gray-500">{{ jsonImportFileName }}</span>
          </div>

          <textarea
            v-model="jsonImportRaw"
            rows="10"
            placeholder='Pega aquí el JSON completo de la propuesta...'
            class="w-full px-4 py-3 border border-gray-200 rounded-xl text-xs font-mono leading-relaxed
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-y"
            @input="parseImportJson"
          />

          <!-- Parse error -->
          <div v-if="jsonImportError" class="mt-2 text-sm text-red-600 bg-red-50 px-4 py-2 rounded-lg">
            {{ jsonImportError }}
          </div>

          <!-- Preview -->
          <div v-if="jsonImportParsed && !jsonImportError" class="mt-3 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3">
            <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
              <span><span class="text-gray-500">Cliente:</span> <span class="font-medium text-gray-900">{{ jsonImportPreview.clientName }}</span></span>
              <span><span class="text-gray-500">Secciones:</span> <span class="font-medium text-gray-900">{{ jsonImportPreview.sectionCount }}</span></span>
              <span v-if="jsonImportPreview.investment"><span class="text-gray-500">Inversión:</span> <span class="font-medium text-gray-900">{{ jsonImportPreview.investment }}</span></span>
            </div>
          </div>

          <!-- Apply button -->
          <div v-if="jsonImportParsed && !jsonImportError" class="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              :disabled="proposalStore.isUpdating"
              class="px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                     hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
              @click="handleApplyImportJson"
            >
              {{ proposalStore.isUpdating ? 'Aplicando...' : 'Aplicar JSON' }}
            </button>
            <p class="text-xs text-gray-400">Esto reemplazará la metadata y todas las secciones de la propuesta.</p>
          </div>

          <!-- Import result message -->
          <div v-if="jsonImportMsg" class="mt-3 text-sm px-4 py-3 rounded-xl" :class="jsonImportMsg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'">
            {{ jsonImportMsg.text }}
          </div>
        </div>
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
        <!-- F10: Section completeness indicator -->
        <div v-if="allSections.length" class="mb-4 bg-white rounded-xl shadow-sm border border-gray-100 px-5 py-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">Completitud de secciones</span>
            <span class="text-sm font-bold" :class="sectionCompleteness >= 80 ? 'text-emerald-600' : sectionCompleteness >= 50 ? 'text-amber-600' : 'text-red-500'">
              {{ sectionCompleteness }}%
            </span>
          </div>
          <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="sectionCompleteness >= 80 ? 'bg-emerald-500' : sectionCompleteness >= 50 ? 'bg-amber-500' : 'bg-red-400'"
              :style="{ width: sectionCompleteness + '%' }"
            />
          </div>
          <p class="text-[11px] text-gray-400 mt-1.5">
            {{ sectionsWithContent }}/{{ enabledSectionsCount }} secciones habilitadas tienen contenido
          </p>
        </div>

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
                <span class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ section.title }}</span>
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
                @syncHostingPercent="handleSyncHostingPercent"
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

    <!-- Pre-send scorecard modal -->
    <Teleport to="body">
      <div v-if="showSendChecklist" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/40 backdrop-blur-sm" @click.self="showSendChecklist = false">
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-6 sm:p-8">
          <div class="flex items-center justify-between mb-1">
            <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">Scorecard pre-envío</h3>
            <span v-if="scorecardData" class="text-sm font-bold px-2.5 py-1 rounded-full"
              :class="scorecardData.score >= 8 ? 'bg-emerald-100 text-emerald-700' : scorecardData.score >= 5 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'">
              {{ scorecardData.score }}/10
            </span>
          </div>
          <p class="text-sm text-gray-500 mb-5">{{ scorecardLoading ? 'Verificando...' : 'Verifica que todo esté listo antes de enviar.' }}</p>
          <ul v-if="!scorecardLoading" class="space-y-3 mb-6">
            <li v-for="(item, idx) in sendChecklist" :key="idx" class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full flex items-center justify-center text-sm flex-shrink-0"
                :class="item.pass ? 'bg-emerald-100 text-emerald-600' : item.blocker ? 'bg-red-100 text-red-500' : 'bg-amber-100 text-amber-500'">
                {{ item.pass ? '✓' : '✗' }}
              </span>
              <div class="flex-1 min-w-0">
                <span class="text-sm" :class="item.pass ? 'text-gray-700' : item.blocker ? 'text-red-600 font-medium' : 'text-amber-600'">{{ item.label }}</span>
                <span v-if="!item.pass && item.blocker" class="ml-1 text-[10px] text-red-400 font-semibold uppercase">bloqueante</span>
              </div>
            </li>
          </ul>
          <div v-else class="flex items-center justify-center py-8">
            <span class="text-sm text-gray-400">Cargando scorecard...</span>
          </div>
          <div class="flex gap-3 justify-end">
            <button class="px-5 py-2.5 bg-gray-100 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors" @click="showSendChecklist = false">
              Cancelar
            </button>
            <button
              class="px-5 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
              :disabled="!allChecksPassing || scorecardLoading"
              @click="confirmSend"
            >
              Enviar al Cliente
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Floating refresh button -->
    <button
      type="button"
      class="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg transition-all hover:shadow-xl hover:scale-105 disabled:opacity-50 flex items-center justify-center dark:bg-emerald-700 dark:hover:bg-emerald-600"
      :disabled="isRefreshing"
      :title="isRefreshing ? 'Actualizando...' : 'Actualizar datos'"
      @click="refreshData"
    >
      <svg class="w-5 h-5" :class="{ 'animate-spin': isRefreshing }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import SectionEditor from '~/components/BusinessProposal/admin/SectionEditor.vue';
import ProposalAnalytics from '~/components/BusinessProposal/admin/ProposalAnalytics.vue';
import ResponsiveTabs from '~/components/ui/ResponsiveTabs.vue';
import { useConfirmModal } from '~/composables/useConfirmModal';
import { useSellerPrompt } from '~/composables/useSellerPrompt';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const route = useRoute();
const proposalStore = useProposalStore();
const { confirmState, requestConfirm, handleConfirmed, handleCancelled } = useConfirmModal();

const proposal = computed(() => proposalStore.currentProposal);
const allSections = computed(() =>
  [...(proposal.value?.sections || [])].sort((a, b) => a.order - b.order)
);

const enabledSectionsCount = computed(() =>
  allSections.value.filter(s => s.is_enabled).length
);

const sectionsWithContent = computed(() => {
  return allSections.value.filter(s => {
    if (!s.is_enabled) return false;
    let cj = s.content_json;
    if (typeof cj === 'string') {
      try { cj = JSON.parse(cj); } catch { cj = null; }
    }
    return cj && typeof cj === 'object' && Object.keys(cj).length > 0;
  }).length;
});

const sectionCompleteness = computed(() => {
  if (enabledSectionsCount.value === 0) return 0;
  return Math.round(sectionsWithContent.value / enabledSectionsCount.value * 100);
});

const activeTab = ref('general');
const tabs = [
  { id: 'general', label: 'General' },
  { id: 'sections', label: 'Secciones' },
  { id: 'prompt', label: 'Prompt Proposal' },
  { id: 'json', label: 'JSON' },
  { id: 'activity', label: 'Actividad' },
  { id: 'analytics', label: 'Analytics' },
];

// ── Prompt Proposal ──
const {
  promptText,
  isEditing: promptIsEditing,
  DEFAULT_PROMPT: promptDefault,
  loadSavedPrompt,
  savePrompt: promptSave,
  resetPrompt: promptReset,
  copyPrompt: promptCopy,
  downloadPrompt: promptDownload,
} = useSellerPrompt();

const promptEditBuffer = ref('');
const promptCopied = ref(false);

function startEditPrompt() {
  promptEditBuffer.value = promptText.value;
  promptIsEditing.value = true;
}
function cancelEditPrompt() {
  promptIsEditing.value = false;
}
function saveEditPrompt() {
  promptSave(promptEditBuffer.value);
  promptIsEditing.value = false;
}
async function handleCopyPrompt() {
  await promptCopy();
  promptCopied.value = true;
  setTimeout(() => { promptCopied.value = false; }, 2000);
}
function handleResetPrompt() {
  promptReset();
}

const isRefreshing = ref(false);
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
  hosting_percent: 30,
  hosting_discount_semiannual: 20,
  hosting_discount_quarterly: 10,
  expires_at: '',
  reminder_days: 10,
  urgency_reminder_days: 15,
  discount_percent: 0,
  automations_paused: false,
});

onMounted(async () => {
  const id = route.params.id;
  await proposalStore.fetchProposal(id);
  loadSavedPrompt();
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
      hosting_percent: proposal.value.hosting_percent ?? 30,
      hosting_discount_semiannual: proposal.value.hosting_discount_semiannual ?? 20,
      hosting_discount_quarterly: proposal.value.hosting_discount_quarterly ?? 10,
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

async function refreshData() {
  isRefreshing.value = true;
  try {
    await proposalStore.fetchProposal(route.params.id);
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
        hosting_percent: proposal.value.hosting_percent ?? 30,
        hosting_discount_semiannual: proposal.value.hosting_discount_semiannual ?? 20,
        hosting_discount_quarterly: proposal.value.hosting_discount_quarterly ?? 10,
        expires_at: proposal.value.expires_at
          ? proposal.value.expires_at.slice(0, 16)
          : '',
        reminder_days: proposal.value.reminder_days,
        urgency_reminder_days: proposal.value.urgency_reminder_days ?? 15,
        discount_percent: proposal.value.discount_percent ?? 0,
        automations_paused: proposal.value.automations_paused ?? false,
      });
    }
  } finally {
    isRefreshing.value = false;
  }
}

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
const scorecardData = ref(null);
const scorecardLoading = ref(false);

const sendChecklist = computed(() => {
  if (scorecardData.value?.checks) {
    return scorecardData.value.checks.map(c => ({
      label: c.label,
      pass: c.passed,
      blocker: c.blocker,
    }));
  }
  // Fallback to local checks if scorecard hasn't loaded
  return [
    { label: 'Email del cliente configurado', pass: !!form.client_email?.trim(), blocker: true },
    { label: 'Nombre del cliente', pass: !!form.client_name?.trim(), blocker: true },
    { label: 'Inversión > $0', pass: Number(form.total_investment) > 0, blocker: true },
    { label: 'Fecha de expiración futura', pass: !!form.expires_at && new Date(form.expires_at) > new Date(), blocker: true },
    { label: 'Al menos 1 sección habilitada', pass: allSections.value?.some(s => s.is_enabled), blocker: true },
  ];
});

const allChecksPassing = computed(() => {
  if (scorecardData.value) {
    return scorecardData.value.can_send !== false;
  }
  return sendChecklist.value.filter(c => c.blocker).every(c => c.pass);
});

async function handleSend() {
  showSendChecklist.value = true;
  scorecardLoading.value = true;
  try {
    const result = await proposalStore.fetchScorecard(proposal.value.id);
    if (result.success) {
      scorecardData.value = result.data;
    }
  } catch (_e) { /* use local fallback */ }
  scorecardLoading.value = false;
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

function handleResend() {
  requestConfirm({
    title: 'Re-enviar propuesta',
    message: '¿Re-enviar esta propuesta? Se mantendrá la misma fecha de expiración.',
    variant: 'info',
    confirmText: 'Re-enviar',
    onConfirm: async () => {
      const result = await proposalStore.resendProposal(proposal.value.id);
      if (result.success) {
        updateMsg.value = { type: 'success', text: 'Propuesta re-enviada al cliente.' };
      } else {
        updateMsg.value = { type: 'error', text: result.errors?.error || 'Error al re-enviar.' };
      }
    },
  });
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

async function handleSyncHostingPercent(percent) {
  if (form.hosting_percent !== percent) {
    form.hosting_percent = percent;
    await proposalStore.updateProposal(proposal.value.id, { hosting_percent: percent });
  }
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

// --- JSON tab ---
const EXPECTED_SECTION_KEYS = [
  'general', 'executiveSummary', 'contextDiagnostic', 'conversionStrategy',
  'designUX', 'creativeSupport', 'developmentStages', 'processMethodology',
  'functionalRequirements', 'timeline', 'investment', 'proposalSummary',
  'finalNote', 'nextSteps',
];

const jsonExportLoading = ref(false);
const exportJsonData = ref(null);
const jsonCopied = ref(false);

const jsonImportRaw = ref('');
const jsonImportParsed = ref(null);
const jsonImportError = ref('');
const jsonImportFileName = ref('');
const jsonImportMsg = ref(null);

const exportJsonString = computed(() => {
  if (!exportJsonData.value) return '';
  return JSON.stringify(exportJsonData.value, null, 2);
});

const jsonImportPreview = computed(() => {
  if (!jsonImportParsed.value) return {};
  const p = jsonImportParsed.value;
  const clientName = p.general?.clientName || '';
  const sectionCount = EXPECTED_SECTION_KEYS.filter((k) => k in p).length;
  const investment = p.investment?.totalInvestment || '';
  return { clientName, sectionCount, investment };
});

async function refreshExportJson() {
  if (!proposal.value?.id) return;
  jsonExportLoading.value = true;
  try {
    const result = await proposalStore.exportProposalJSON(proposal.value.id);
    if (result.success) {
      exportJsonData.value = result.data;
    }
  } finally {
    jsonExportLoading.value = false;
  }
}

async function copyExportJson() {
  if (!exportJsonString.value) return;
  try {
    await navigator.clipboard.writeText(exportJsonString.value);
    jsonCopied.value = true;
    setTimeout(() => { jsonCopied.value = false; }, 2000);
  } catch (e) {
    console.error('Copy failed:', e);
  }
}

function downloadExportJson() {
  if (!exportJsonString.value || !proposal.value) return;
  const blob = new Blob([exportJsonString.value], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `proposal-${proposal.value.uuid || proposal.value.id}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function parseImportJson() {
  jsonImportError.value = '';
  jsonImportParsed.value = null;
  jsonImportMsg.value = null;

  const raw = jsonImportRaw.value.trim();
  if (!raw) return;

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    jsonImportError.value = 'JSON inválido. Revisa la sintaxis.';
    return;
  }

  if (typeof parsed !== 'object' || Array.isArray(parsed)) {
    jsonImportError.value = 'El JSON debe ser un objeto, no un array.';
    return;
  }

  if (!parsed.general || !parsed.general.clientName) {
    jsonImportError.value = 'El JSON debe incluir "general" con "clientName".';
    return;
  }

  jsonImportParsed.value = parsed;
}

function handleJsonFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  jsonImportFileName.value = file.name;

  const reader = new FileReader();
  reader.onload = (e) => {
    jsonImportRaw.value = e.target.result;
    parseImportJson();
  };
  reader.readAsText(file);
}

function parseInvestmentString(str) {
  if (!str) return 0;
  if (typeof str === 'number') return str;
  const cleaned = String(str).replace(/[^0-9]/g, '');
  return cleaned ? Number(cleaned) : 0;
}

async function handleApplyImportJson() {
  if (!jsonImportParsed.value || !proposal.value?.id) return;

  const confirmed = await requestConfirm({
    title: 'Aplicar JSON',
    message: 'Esto reemplazará la metadata y todas las secciones de la propuesta. ¿Continuar?',
    variant: 'warning',
    confirmText: 'Aplicar',
    cancelText: 'Cancelar',
  });
  if (!confirmed) return;

  jsonImportMsg.value = null;

  const sections = { ...jsonImportParsed.value };
  delete sections._meta;
  delete sections._seller_prompt;

  const meta = jsonImportParsed.value._meta || {};
  const payload = {
    title: meta.title || proposal.value.title,
    client_name: jsonImportParsed.value.general?.clientName || proposal.value.client_name,
    client_email: meta.client_email || proposal.value.client_email || '',
    client_phone: meta.client_phone || proposal.value.client_phone || '',
    project_type: meta.project_type || proposal.value.project_type || '',
    market_type: meta.market_type || proposal.value.market_type || '',
    project_type_custom: meta.project_type_custom || proposal.value.project_type_custom || '',
    market_type_custom: meta.market_type_custom || proposal.value.market_type_custom || '',
    language: meta.language || proposal.value.language || 'es',
    total_investment: parseInvestmentString(meta.total_investment || jsonImportParsed.value.investment?.totalInvestment) || Number(proposal.value.total_investment) || 0,
    currency: meta.currency || jsonImportParsed.value.investment?.currency || proposal.value.currency || 'COP',
    expires_at: meta.expires_at || (proposal.value.expires_at ? proposal.value.expires_at : null),
    reminder_days: meta.reminder_days || proposal.value.reminder_days || 10,
    urgency_reminder_days: meta.urgency_reminder_days || proposal.value.urgency_reminder_days || 15,
    discount_percent: meta.discount_percent ?? proposal.value.discount_percent ?? 0,
    sections,
  };

  const result = await proposalStore.updateProposalFromJSON(proposal.value.id, payload);
  if (result.success) {
    jsonImportMsg.value = { type: 'success', text: 'Propuesta actualizada desde JSON.' };
    jsonImportRaw.value = '';
    jsonImportParsed.value = null;
    jsonImportFileName.value = '';

    // Sync local form with updated proposal
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
        hosting_percent: proposal.value.hosting_percent ?? 30,
        hosting_discount_semiannual: proposal.value.hosting_discount_semiannual ?? 20,
        hosting_discount_quarterly: proposal.value.hosting_discount_quarterly ?? 10,
        expires_at: proposal.value.expires_at ? proposal.value.expires_at.slice(0, 16) : '',
        reminder_days: proposal.value.reminder_days,
        urgency_reminder_days: proposal.value.urgency_reminder_days ?? 15,
        discount_percent: proposal.value.discount_percent ?? 0,
        automations_paused: proposal.value.automations_paused ?? false,
      });
    }

    // Refresh the export JSON view
    await refreshExportJson();
  } else {
    const errors = result.errors;
    jsonImportMsg.value = {
      type: 'error',
      text: errors
        ? (typeof errors === 'object'
          ? Object.entries(errors).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
          : String(errors))
        : 'Error al aplicar el JSON.',
    };
  }
}

// Auto-load JSON export when switching to json tab
watch(activeTab, (newTab) => {
  if (newTab === 'json' && proposal.value?.id) {
    refreshExportJson();
  }
});

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
