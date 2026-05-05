<template>
  <div>
    <div class="mb-8">
      <NuxtLink :to="localePath('/panel/proposals')" class="text-sm text-text-muted hover:text-text-default transition-colors">
        ← Volver a propuestas
      </NuxtLink>
      <h1 class="text-2xl font-light text-text-default mt-2">Nueva Propuesta</h1>
    </div>

    <!-- Tab toggle -->
    <div class="flex gap-1 mb-6 bg-surface-raised rounded-xl p-1 w-full max-w-md">
      <button
        type="button"
        :class="[
          'flex-1 min-w-0 px-2 sm:px-4 py-2 text-xs sm:text-sm rounded-lg transition-all whitespace-nowrap truncate',
          mode === 'json' ? 'bg-surface shadow-sm font-medium text-text-default' : 'text-text-muted hover:text-text-default'
        ]"
        @click="mode = 'json'"
      >
        <span class="sm:hidden">JSON</span>
        <span class="hidden sm:inline">Importar JSON</span>
      </button>
      <button
        type="button"
        :class="[
          'flex-1 min-w-0 px-2 sm:px-4 py-2 text-xs sm:text-sm rounded-lg transition-all whitespace-nowrap truncate',
          mode === 'prompt' ? 'bg-surface shadow-sm font-medium text-text-default' : 'text-text-muted hover:text-text-default'
        ]"
        @click="mode = 'prompt'"
      >
        <span class="sm:hidden">Prompt</span>
        <span class="hidden sm:inline">Prompt IA</span>
      </button>
      <button
        type="button"
        :class="[
          'flex-1 min-w-0 px-2 sm:px-4 py-2 text-xs sm:text-sm rounded-lg transition-all whitespace-nowrap truncate',
          mode === 'manual' ? 'bg-surface shadow-sm font-medium text-text-default' : 'text-text-muted hover:text-text-default'
        ]"
        @click="mode = 'manual'"
      >
        Manual
      </button>
    </div>

    <!-- ============================================================ -->
    <!-- MANUAL MODE (existing form, unchanged) -->
    <!-- ============================================================ -->
    <form v-if="mode === 'manual'" class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-8 max-w-2xl" @submit.prevent="handleSubmit">
      <div class="space-y-6">
        <!-- Title -->
        <div>
          <label for="create-title" class="block text-sm font-medium text-text-default mb-1">Título</label>
          <input
            id="create-title"
            v-model="form.title"
            type="text"
            required
            placeholder="Propuesta Desarrollo Web — Cliente"
            class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
          />
        </div>

        <!-- Client picker (autocomplete + snapshot fields) -->
        <div class="space-y-4 border border-border-muted rounded-xl p-4 bg-surface-raised">
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Cliente</label>
            <ClientAutocomplete
              v-model="form.client_id"
              :initial-label="form.client_name"
              @select="onClientSelected"
              @create-new="onCreateInlineClient"
            />
            <p class="text-xs text-text-subtle mt-1">
              Busca un cliente existente o escribe uno nuevo. Si no tiene email, generaremos uno temporal y pausaremos automatizaciones hasta que lo agregues.
            </p>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label for="create-client-name" class="block text-xs font-medium text-text-muted mb-1">Nombre</label>
              <input
                id="create-client-name"
                v-model="form.client_name"
                type="text"
                required
                placeholder="María García"
                class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div>
              <label for="create-client-email" class="block text-xs font-medium text-text-muted mb-1">Email</label>
              <input
                id="create-client-email"
                v-model="form.client_email"
                type="email"
                placeholder="maria@gmail.com (opcional)"
                class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Teléfono / WhatsApp</label>
              <input
                v-model="form.client_phone"
                type="tel"
                placeholder="+57 300 123 4567"
                class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Empresa</label>
              <input
                v-model="form.client_company"
                type="text"
                placeholder="Acme Inc."
                class="w-full px-3 py-2 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
          </div>
        </div>

        <!-- Project type + Market type -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Tipo de proyecto</label>
            <select v-model="form.project_type" class="w-full px-4 py-2.5 border border-border-default dark:border-white/[0.08] rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none bg-surface dark:text-white">
              <option value="">— Sin definir —</option>
              <option value="website">Sitio Web</option>
              <option value="ecommerce">E-commerce</option>
              <option value="webapp">Aplicación Web</option>
              <option value="landing">Landing Page</option>
              <option value="redesign">Rediseño</option>
              <option value="mobile_app">App Móvil</option>
              <option value="branding">Branding / Identidad Visual</option>
              <option value="cms">Sistema CMS</option>
              <option value="portal">Portal / Intranet</option>
              <option value="api_integration">Integración de APIs</option>
              <option value="marketplace">Marketplace</option>
              <option value="erp">Sistema ERP / Administrativo</option>
              <option value="booking">Sistema de Reservas</option>
              <option value="dashboard">Dashboard / Reportes</option>
              <option value="crm">Sistema CRM</option>
              <option value="saas">SaaS / Plataforma</option>
              <option value="chatbot">Chatbot / Asistente Virtual</option>
              <option value="ai_tool">Herramienta con IA</option>
              <option value="automation">Automatización / RPA</option>
              <option value="data_analytics">Analítica de Datos / BI</option>
              <option value="plugin_extension">Plugin / Extensión</option>
              <option value="other">Otro</option>
            </select>
            <input
              v-if="form.project_type === 'other'"
              v-model="form.project_type_custom"
              type="text"
              placeholder="Especificar tipo de proyecto..."
              class="mt-2 w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Tipo de mercado</label>
            <select v-model="form.market_type" class="w-full px-4 py-2.5 border border-border-default dark:border-white/[0.08] rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none bg-surface dark:text-white">
              <option value="">— Sin definir —</option>
              <option value="b2b">B2B</option>
              <option value="b2c">B2C</option>
              <option value="saas">SaaS</option>
              <option value="retail">Retail</option>
              <option value="services">Servicios profesionales</option>
              <option value="health">Salud</option>
              <option value="education">Educación</option>
              <option value="real_estate">Inmobiliaria</option>
              <option value="fintech">Fintech / Finanzas</option>
              <option value="restaurant">Restaurantes / F&amp;B</option>
              <option value="tourism">Turismo / Hospitalidad</option>
              <option value="logistics">Logística / Transporte</option>
              <option value="sports">Deportes / Fitness</option>
              <option value="legal">Servicios Legales / Jurídico</option>
              <option value="construction">Construcción / Arquitectura</option>
              <option value="media">Medios / Entretenimiento</option>
              <option value="ngo">ONG / Sector Público</option>
              <option value="agriculture">Agro / Tecnología Agrícola</option>
              <option value="tech">Tecnología / Software</option>
              <option value="consulting">Consultoría / Asesoría</option>
              <option value="automotive">Automotriz</option>
              <option value="fashion">Moda / Textil</option>
              <option value="beauty">Belleza / Cuidado Personal</option>
              <option value="manufacturing">Manufactura / Industrial</option>
              <option value="energy">Energía / Utilities</option>
              <option value="gaming">Videojuegos / Gaming</option>
              <option value="other">Otro</option>
            </select>
            <input
              v-if="form.market_type === 'other'"
              v-model="form.market_type_custom"
              type="text"
              placeholder="Especificar tipo de mercado..."
              class="mt-2 w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
        </div>

        <!-- Language -->
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Idioma de la propuesta</label>
          <select
            v-model="form.language"
            class="w-full px-4 py-2.5 border border-border-default dark:border-white/[0.08] rounded-xl text-sm
                   focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none bg-surface dark:text-white"
          >
            <option value="es">Español</option>
            <option value="en">English</option>
          </select>
          <p class="text-xs text-text-subtle mt-1">Define los títulos e índices por defecto de las secciones.</p>
        </div>

        <!-- Investment + Currency -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Inversión total</label>
            <input
              v-model.number="form.total_investment"
              type="number"
              min="0"
              step="0.01"
              placeholder="3500000"
              class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Moneda</label>
            <select
              v-model="form.currency"
              class="w-full px-4 py-2.5 border border-border-default dark:border-white/[0.08] rounded-xl text-sm
                     focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none bg-surface dark:text-white"
            >
              <option value="COP">COP</option>
              <option value="USD">USD</option>
            </select>
          </div>
        </div>

        <!-- Hosting percent -->
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Hosting (% de inversión total)</label>
          <div class="flex items-center gap-3">
            <input
              v-model.number="form.hosting_percent"
              type="number"
              min="0"
              max="100"
              class="w-32 px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
            <span class="text-sm text-text-muted">%</span>
          </div>
          <div v-if="form.hosting_percent > 0 && form.total_investment > 0" class="mt-3 bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 rounded-xl overflow-hidden">
            <div class="grid grid-cols-[1fr_auto] gap-x-4 text-sm divide-y divide-blue-100 dark:divide-blue-500/20">
              <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">Mensual</div>
              <div class="px-4 py-2 text-blue-800 dark:text-blue-200 font-semibold text-right">
                ${{ Math.round(form.total_investment * form.hosting_percent / 100 / 12).toLocaleString() }} {{ form.currency }}
              </div>
              <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">Trimestral</div>
              <div class="px-4 py-2 text-blue-800 dark:text-blue-200 font-semibold text-right">
                ${{ Math.round(form.total_investment * form.hosting_percent / 100 / 12 * 3).toLocaleString() }} {{ form.currency }}
              </div>
              <template v-if="form.hosting_discount_quarterly">
                <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">
                  Trimestral
                  <span class="ml-1 text-xs text-text-brand font-normal">({{ form.hosting_discount_quarterly }}% dcto)</span>
                </div>
                <div class="px-4 py-2 text-text-brand font-semibold text-right">
                  ${{ Math.round(Math.round(form.total_investment * form.hosting_percent / 100 / 12) * (100 - form.hosting_discount_quarterly) / 100 * 3).toLocaleString() }} {{ form.currency }}
                </div>
              </template>
              <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">Semestral</div>
              <div class="px-4 py-2 text-blue-800 dark:text-blue-200 font-semibold text-right">
                ${{ Math.round(form.total_investment * form.hosting_percent / 100 / 12 * 6).toLocaleString() }} {{ form.currency }}
              </div>
              <template v-if="form.hosting_discount_semiannual">
                <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">
                  Semestral
                  <span class="ml-1 text-xs text-text-brand font-normal">({{ form.hosting_discount_semiannual }}% dcto)</span>
                </div>
                <div class="px-4 py-2 text-text-brand font-semibold text-right">
                  ${{ Math.round(Math.round(form.total_investment * form.hosting_percent / 100 / 12) * (100 - form.hosting_discount_semiannual) / 100 * 6).toLocaleString() }} {{ form.currency }}
                </div>
              </template>
              <div class="px-4 py-2 text-blue-700 dark:text-blue-300 font-medium">☁️ Anual</div>
              <div class="px-4 py-2 text-blue-800 dark:text-blue-200 font-semibold text-right">
                ${{ Math.round(form.total_investment * form.hosting_percent / 100).toLocaleString() }} {{ form.currency }}
              </div>
            </div>
          </div>
          <p class="text-xs text-text-subtle mt-1">Se sincroniza con el % del Plan de Hosting en la sección "Tu inversión y cómo pagar".</p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Dcto. semestral (%)</label>
            <input v-model.number="form.hosting_discount_semiannual" type="number" min="0" max="100"
              class="w-32 px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Dcto. trimestral (%)</label>
            <input v-model.number="form.hosting_discount_quarterly" type="number" min="0" max="100"
              class="w-32 px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none" />
          </div>
        </div>

        <!-- Expires at -->
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Fecha de expiración</label>
          <div class="flex items-center gap-2">
            <input
              v-model="form.expires_at"
              type="datetime-local"
              class="flex-1 px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
            <input
              v-model.number="expiryDaysInput"
              type="number"
              min="1"
              max="365"
              class="w-20 px-3 py-2.5 border border-input-border bg-input-bg text-input-text rounded-xl text-sm text-center focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
            <span class="text-xs text-text-subtle whitespace-nowrap">días</span>
          </div>
        </div>

        <!-- Reminder days -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Recordatorio (días después de enviar)</label>
            <input
              v-model.number="form.reminder_days"
              type="number"
              min="1"
              max="30"
              class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
            <p class="text-xs text-text-subtle mt-1">Se enviará un email recordatorio al cliente X días después de enviar la propuesta.</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-text-default mb-1">Urgencia (días después de enviar)</label>
            <input
              v-model.number="form.urgency_reminder_days"
              type="number"
              min="1"
              max="30"
              class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
            <p class="text-xs text-text-subtle mt-1">Se enviará un email de urgencia X días después de enviar (incluye descuento si % > 0).</p>
          </div>
        </div>

        <!-- Discount -->
        <div>
          <label class="block text-sm font-medium text-text-default mb-1">Descuento (%)</label>
          <input
            v-model.number="form.discount_percent"
            type="number"
            min="0"
            max="100"
            class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
          />
          <p class="text-xs text-text-subtle mt-1">Si es mayor a 0, se enviará un email de urgencia con descuento 2 días antes de expirar. 0 = sin descuento.</p>
        </div>

        <!-- Errors -->
        <div v-if="errorMsg" class="text-sm text-red-600 dark:text-red-300 bg-red-50 dark:bg-red-500/10 px-4 py-3 rounded-xl">
          {{ errorMsg }}
        </div>

        <!-- Submit -->
        <div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3 sm:gap-4 pt-2">
          <button
            type="submit"
            :disabled="proposalStore.isUpdating"
            class="w-full sm:w-auto px-5 sm:px-6 py-2.5 bg-primary text-on-primary rounded-xl font-medium text-sm
                   hover:bg-primary-strong transition-colors shadow-sm disabled:opacity-50"
          >
            {{ proposalStore.isUpdating ? 'Creando...' : 'Crear Propuesta' }}
          </button>
          <button
            v-if="canSendDirectly"
            type="button"
            :disabled="proposalStore.isUpdating"
            class="w-full sm:w-auto px-5 sm:px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm
                   hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50"
            @click="handleCreateAndSend"
          >
            {{ proposalStore.isUpdating ? 'Creando...' : 'Crear y Enviar' }}
          </button>
          <NuxtLink :to="localePath('/panel/proposals')" class="text-sm text-text-muted hover:text-text-default text-center sm:text-left">
            Cancelar
          </NuxtLink>
        </div>
        <p v-if="canSendDirectly" class="text-xs text-text-subtle mt-2">Envía directamente si los datos del cliente están completos.</p>
      </div>
    </form>

    <!-- ============================================================ -->
    <!-- JSON IMPORT MODE -->
    <!-- ============================================================ -->
    <div v-else-if="mode === 'json'" class="max-w-3xl space-y-6">

      <!-- Download template row -->
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 class="text-sm font-medium text-text-default">Plantilla JSON</h3>
            <p class="text-xs text-text-subtle mt-0.5">Incluye secciones comerciales y la clave <code class="text-[10px]">technicalDocument</code> (detalle técnico).</p>
          </div>
          <div class="flex items-center gap-3">
            <select
              v-model="jsonForm.language"
              class="px-3 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm bg-surface dark:text-white
                     focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none"
            >
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-default bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
              @click="copyTemplate"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              {{ templateCopied ? '¡Copiado!' : 'Copiar' }}
            </button>
            <button
              type="button"
              :disabled="isDownloading"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-default bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors disabled:opacity-50"
              @click="downloadTemplate"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              {{ isDownloading ? 'Descargando...' : 'Descargar' }}
            </button>
          </div>
        </div>
      </div>

      <!-- JSON input -->
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
        <h3 class="text-sm font-medium text-text-default mb-3">Pegar o subir JSON</h3>

        <div class="flex items-center gap-3 mb-3">
          <label
            class="inline-flex items-center gap-2 px-4 py-2 border border-border-default dark:border-white/[0.08] rounded-lg text-sm
                   text-text-default hover:bg-surface-raised cursor-pointer transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Subir archivo .json
            <input type="file" accept=".json" class="hidden" @change="handleFileUpload" />
          </label>
          <span v-if="uploadedFileName" class="text-xs text-text-muted">{{ uploadedFileName }}</span>
        </div>

        <textarea
          v-model="jsonRaw"
          rows="14"
          placeholder='{ "general": { "clientName": "..." }, "executiveSummary": { ... }, ... }'
          class="w-full px-4 py-3 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-xs font-mono leading-relaxed focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-y"
          @input="parseJson"
        ></textarea>

        <!-- Parse error -->
        <div v-if="jsonError" class="mt-2 text-sm text-red-600 dark:text-red-300 bg-red-50 dark:bg-red-500/10 px-4 py-2 rounded-lg">
          {{ jsonError }}
        </div>

        <!-- Preview -->
        <div v-if="jsonParsed && !jsonError" class="mt-3 bg-primary-soft border border-emerald-200 dark:border-emerald-500/20 rounded-lg px-4 py-3">
          <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span><span class="text-text-muted">Cliente:</span> <span class="font-medium text-text-default">{{ jsonPreview.clientName }}</span></span>
            <span><span class="text-text-muted">Secciones:</span> <span class="font-medium text-text-default">{{ jsonPreview.sectionCount }}</span></span>
            <span v-if="jsonPreview.epicCount != null"><span class="text-text-muted">Módulos (det. técnico):</span> <span class="font-medium text-text-default">{{ jsonPreview.epicCount }}</span></span>
            <span v-if="jsonPreview.investment"><span class="text-text-muted">Inversión:</span> <span class="font-medium text-text-default">{{ jsonPreview.investment }}</span></span>
          </div>
        </div>

        <LegacyFormatWarning
          v-if="jsonParsed && !jsonError"
          :issues="legacyFormatIssues"
          :field-labels="LEGACY_FIELD_LABELS"
          @download="downloadMigratedProposalJson(jsonParsed)"
        />
      </div>

      <!-- Metadata form -->
      <form v-if="jsonParsed && !jsonError && !legacyFormatIssues.length" class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6" @submit.prevent="handleJsonSubmit">
        <h3 class="text-sm font-medium text-text-default mb-4">Datos de la propuesta</h3>
        <div class="space-y-4">
          <!-- Title -->
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Título</label>
            <input
              v-model="jsonForm.title"
              type="text"
              required
              class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>

          <!-- Client email -->
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Email del cliente</label>
            <input
              v-model="jsonForm.client_email"
              type="email"
              placeholder="cliente@example.com"
              class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
            />
          </div>

          <!-- Investment + Currency -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Inversión total</label>
              <input
                v-model.number="jsonForm.total_investment"
                type="number"
                min="0"
                step="0.01"
                class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Moneda</label>
              <select
                v-model="jsonForm.currency"
                class="w-full px-4 py-2.5 border border-border-default dark:border-white/[0.08] rounded-xl text-sm
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none bg-surface dark:text-white"
              >
                <option value="COP">COP</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>

          <!-- Project type / Market type -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Tipo de proyecto</label>
              <select v-model="jsonForm.project_type"
                class="w-full px-4 py-2.5 border border-border-default dark:border-white/[0.08] rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none bg-surface dark:text-white">
                <option value="">— Sin definir —</option>
                <option value="website">Sitio Web</option>
                <option value="ecommerce">E-commerce</option>
                <option value="webapp">Aplicación Web</option>
                <option value="landing">Landing Page</option>
                <option value="redesign">Rediseño</option>
                <option value="mobile_app">App Móvil</option>
                <option value="branding">Branding / Identidad Visual</option>
                <option value="cms">Sistema CMS</option>
                <option value="portal">Portal / Intranet</option>
                <option value="api_integration">Integración de APIs</option>
                <option value="marketplace">Marketplace</option>
                <option value="erp">Sistema ERP / Administrativo</option>
                <option value="booking">Sistema de Reservas</option>
                <option value="dashboard">Dashboard / Reportes</option>
                <option value="crm">Sistema CRM</option>
                <option value="saas">SaaS / Plataforma</option>
                <option value="chatbot">Chatbot / Asistente Virtual</option>
                <option value="ai_tool">Herramienta con IA</option>
                <option value="automation">Automatización / RPA</option>
                <option value="data_analytics">Analítica de Datos / BI</option>
                <option value="plugin_extension">Plugin / Extensión</option>
                <option value="other">Otro</option>
              </select>
              <input
                v-if="jsonForm.project_type === 'other'"
                v-model="jsonForm.project_type_custom"
                type="text"
                placeholder="Especificar tipo de proyecto..."
                class="mt-2 w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Tipo de mercado</label>
              <select v-model="jsonForm.market_type"
                class="w-full px-4 py-2.5 border border-border-default dark:border-white/[0.08] rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-emerald-500 outline-none bg-surface dark:text-white">
                <option value="">— Sin definir —</option>
                <option value="b2b">B2B</option>
                <option value="b2c">B2C</option>
                <option value="saas">SaaS</option>
                <option value="retail">Retail</option>
                <option value="services">Servicios profesionales</option>
                <option value="health">Salud</option>
                <option value="education">Educación</option>
                <option value="real_estate">Inmobiliaria</option>
                <option value="fintech">Fintech / Finanzas</option>
                <option value="restaurant">Restaurantes / F&amp;B</option>
                <option value="tourism">Turismo / Hospitalidad</option>
                <option value="logistics">Logística / Transporte</option>
                <option value="sports">Deportes / Fitness</option>
                <option value="legal">Servicios Legales / Jurídico</option>
                <option value="construction">Construcción / Arquitectura</option>
                <option value="media">Medios / Entretenimiento</option>
                <option value="ngo">ONG / Sector Público</option>
                <option value="agriculture">Agro / Tecnología Agrícola</option>
                <option value="tech">Tecnología / Software</option>
                <option value="consulting">Consultoría / Asesoría</option>
                <option value="automotive">Automotriz</option>
                <option value="fashion">Moda / Textil</option>
                <option value="beauty">Belleza / Cuidado Personal</option>
                <option value="manufacturing">Manufactura / Industrial</option>
                <option value="energy">Energía / Utilities</option>
                <option value="gaming">Videojuegos / Gaming</option>
                <option value="other">Otro</option>
              </select>
              <input
                v-if="jsonForm.market_type === 'other'"
                v-model="jsonForm.market_type_custom"
                type="text"
                placeholder="Especificar tipo de mercado..."
                class="mt-2 w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
          </div>

          <!-- Expires at -->
          <div>
            <label class="block text-xs font-medium text-text-muted mb-1">Fecha de expiración</label>
            <div class="flex items-center gap-2">
              <input
                v-model="jsonForm.expires_at"
                type="datetime-local"
                class="flex-1 px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
              <input
                v-model.number="expiryDaysInput"
                type="number"
                min="1"
                max="365"
                class="w-20 px-3 py-2.5 border border-input-border bg-input-bg text-input-text rounded-xl text-sm text-center focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
              <span class="text-xs text-text-subtle whitespace-nowrap">días</span>
            </div>
          </div>

          <!-- Reminder / Urgency / Discount -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Recordatorio (día)</label>
              <input
                v-model.number="jsonForm.reminder_days"
                type="number" min="1" max="30"
                class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Urgencia (día)</label>
              <input
                v-model.number="jsonForm.urgency_reminder_days"
                type="number" min="1" max="30"
                class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-muted mb-1">Descuento (%)</label>
              <input
                v-model.number="jsonForm.discount_percent"
                type="number" min="0" max="100"
                class="w-full px-4 py-2.5 border border-input-border bg-input-bg text-input-text placeholder-input-placeholder rounded-xl text-sm focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
          </div>

          <!-- Errors -->
          <div v-if="errorMsg" class="text-sm text-red-600 dark:text-red-300 bg-red-50 dark:bg-red-500/10 px-4 py-3 rounded-xl">
            {{ errorMsg }}
          </div>

          <!-- Submit -->
          <div class="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-3 sm:gap-4 pt-2">
            <button
              type="submit"
              :disabled="proposalStore.isUpdating"
              class="w-full sm:w-auto px-5 sm:px-6 py-2.5 bg-primary text-on-primary rounded-xl font-medium text-sm
                     hover:bg-primary-strong transition-colors shadow-sm disabled:opacity-50"
            >
              {{ proposalStore.isUpdating ? 'Creando...' : 'Crear desde JSON' }}
            </button>
            <NuxtLink :to="localePath('/panel/proposals')" class="text-sm text-text-muted hover:text-text-default text-center sm:text-left">
              Cancelar
            </NuxtLink>
          </div>
        </div>
      </form>
    </div>

    <!-- ============================================================ -->
    <!-- PROMPT IA MODE -->
    <!-- ============================================================ -->
    <div v-if="mode === 'prompt'" class="max-w-3xl space-y-6">
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-4 sm:p-6">
        <PromptSubTabsPanel v-model="createPromptSubTab">
          <template #commercial>
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div>
              <h3 class="text-sm font-medium text-text-default">Prompt comercial</h3>
              <p class="text-xs text-text-subtle mt-0.5">Para rellenar el JSON de propuesta comercial (plantilla en «Importar JSON»).</p>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-2 mb-4">
            <template v-if="!createCommercialPromptIsEditing">
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-default bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
                @click="startEditCreateCommercialPrompt"
              >
                Editar
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-default bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
                @click="handleCopyCreateCommercialPrompt"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                {{ createCommercialPromptCopied ? '¡Copiado!' : 'Copiar' }}
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-default bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
                @click="createCommercialPromptDownload"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                Descargar .md
              </button>
              <button
                v-if="createCommercialPromptText !== createCommercialPromptDefault"
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                @click="handleResetCreateCommercialPrompt"
              >
                Restaurar original
              </button>
            </template>
            <template v-else>
              <button
                type="button"
                class="px-5 py-2 bg-primary text-on-primary rounded-xl font-medium text-sm hover:bg-primary-strong transition-colors shadow-sm"
                @click="saveEditCreateCommercialPrompt"
              >
                Guardar cambios
              </button>
              <button
                type="button"
                class="px-4 py-2 text-sm font-medium text-text-muted hover:text-text-default transition-colors"
                @click="cancelEditCreateCommercialPrompt"
              >
                Cancelar
              </button>
            </template>
          </div>
          <div v-if="createCommercialPromptIsEditing" class="bg-surface-raised rounded-xl border border-border-default overflow-hidden">
            <textarea
              v-model="createCommercialPromptEditBuffer"
              rows="28"
              class="w-full px-4 sm:px-6 py-4 text-xs font-mono leading-relaxed text-text-default bg-transparent border-0 outline-none resize-y focus:ring-0"
            />
          </div>
          <div v-else class="bg-surface-raised rounded-xl border border-border-default overflow-hidden">
            <div class="px-4 sm:px-6 py-4 max-h-[60vh] overflow-y-auto">
              <pre class="text-xs leading-relaxed text-text-default whitespace-pre-wrap font-mono break-words">{{ createCommercialPromptText }}</pre>
            </div>
          </div>
          <p v-if="createCommercialPromptText !== createCommercialPromptDefault" class="text-xs text-amber-600 dark:text-amber-400 mt-3">
            Prompt personalizado. «Restaurar original» vuelve al texto por defecto.
          </p>
          </template>

          <template #technical>
          <p class="text-sm text-text-muted mb-4">
            Para generar solo la clave <code class="text-xs bg-surface-raised px-1 rounded">technicalDocument</code> del JSON (sin narrativa comercial ni precios). Combínalo con la plantilla que incluye esa clave.
          </p>
          <div class="flex flex-wrap items-center gap-2 mb-4">
            <template v-if="!createTechnicalPromptIsEditing">
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-default bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
                @click="startEditCreateTechnicalPrompt"
              >
                Editar
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-default bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
                @click="handleCopyCreateTechnicalPrompt"
              >
                {{ createTechnicalPromptCopied ? '¡Copiado!' : 'Copiar' }}
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-default bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-surface-raised transition-colors"
                @click="createTechnicalPromptDownload"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                Descargar .md
              </button>
              <button
                v-if="createTechnicalPromptText !== createTechnicalPromptDefault"
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-surface border border-border-default dark:border-white/[0.08] rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                @click="handleResetCreateTechnicalPrompt"
              >
                Restaurar original
              </button>
            </template>
            <template v-else>
              <button
                type="button"
                class="px-5 py-2 bg-primary text-on-primary rounded-xl font-medium text-sm hover:bg-primary-strong transition-colors shadow-sm"
                @click="saveEditCreateTechnicalPrompt"
              >
                Guardar cambios
              </button>
              <button
                type="button"
                class="px-4 py-2 text-sm font-medium text-text-muted hover:text-text-default transition-colors"
                @click="cancelEditCreateTechnicalPrompt"
              >
                Cancelar
              </button>
            </template>
          </div>
          <div v-if="createTechnicalPromptIsEditing" class="bg-surface-raised rounded-xl border border-border-default overflow-hidden">
            <textarea
              v-model="createTechnicalPromptEditBuffer"
              rows="26"
              class="w-full px-4 sm:px-6 py-4 text-xs font-mono leading-relaxed text-text-default bg-transparent border-0 outline-none resize-y focus:ring-0"
            />
          </div>
          <div v-else class="bg-surface-raised rounded-xl border border-border-default overflow-hidden">
            <div class="px-4 sm:px-6 py-4 max-h-[60vh] overflow-y-auto">
              <pre class="text-xs leading-relaxed text-text-default whitespace-pre-wrap font-mono break-words">{{ createTechnicalPromptText }}</pre>
            </div>
          </div>
          <p v-if="createTechnicalPromptText !== createTechnicalPromptDefault" class="text-xs text-amber-600 dark:text-amber-400 mt-3">
            Prompt técnico personalizado. «Restaurar original» vuelve al texto por defecto.
          </p>
          </template>
        </PromptSubTabsPanel>

        <div class="mt-4 bg-blue-50 dark:bg-blue-500/10 border border-blue-200 dark:border-blue-500/20 rounded-lg px-4 py-3">
          <p class="text-xs text-blue-700 dark:text-blue-300">
            <strong>Flujo recomendado:</strong><br/>
            1) Descarga la plantilla JSON desde «Importar JSON» (incluye <code class="text-[11px]">technicalDocument</code>).<br/>
            → 2) Usa el prompt comercial y/o el técnico según lo que quieras generar.<br/>
            → 3) Pega plantilla + prompts en tu IA.<br/>
            → 4) Pega el JSON resultante en «Importar JSON».
          </p>
        </div>
      </div>
    </div>

    <!-- Post-creation interstitial modal -->
    <teleport to="body">
      <div v-if="showPostCreateModal && createdProposal" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div class="bg-surface rounded-2xl shadow-2xl max-w-md w-full mx-4 p-6 sm:p-8 text-center">
          <div class="text-5xl mb-4">✅</div>
          <h3 class="text-xl font-bold text-text-default mb-2">Propuesta creada</h3>
          <p class="text-sm text-text-muted mb-4">{{ createdProposal.title }}</p>
          <div v-if="jsonWarnings.length" class="mb-4 text-left bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-lg px-4 py-3">
            <p class="text-xs font-semibold text-amber-800 dark:text-amber-300 mb-1">⚠️ Advertencias del JSON</p>
            <p v-for="(warn, i) in jsonWarnings" :key="i" class="text-xs text-amber-700 dark:text-amber-400">{{ warn }}</p>
          </div>
          <div class="flex flex-col gap-3">
            <a
              :href="'/proposal/' + createdProposal.uuid + '?preview=1'"
              target="_blank"
              class="w-full px-5 py-2.5 bg-surface-raised text-text-default rounded-xl font-medium text-sm hover:bg-surface-raised transition-colors inline-flex items-center justify-center gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
              Ver Preview
            </a>
            <button
              v-if="canSendDirectly"
              class="w-full px-5 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors"
              :disabled="proposalStore.isUpdating"
              @click="handleSendCreated"
            >
              {{ proposalStore.isUpdating ? 'Enviando...' : 'Enviar al Cliente' }}
            </button>
            <button
              class="w-full px-5 py-2.5 bg-primary text-on-primary rounded-xl font-medium text-sm hover:bg-primary-strong transition-colors"
              @click="router.push(localePath(`/panel/proposals/${createdProposal.id}/edit`))"
            >
              Ir a Editar
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, watch } from 'vue';
import PromptSubTabsPanel from '~/components/panel/PromptSubTabsPanel.vue';
import { get_request } from '~/stores/services/request_http';
import { useSellerPrompt } from '~/composables/useSellerPrompt';
import { useTechnicalPrompt } from '~/composables/useTechnicalPrompt';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { detectLegacyTechnicalFormat, downloadMigratedProposalJson, LEGACY_FIELD_LABELS } from '~/utils/proposalJsonMigration';
import LegacyFormatWarning from '~/components/panel/LegacyFormatWarning.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const router = useRouter();
const proposalStore = useProposalStore();
const errorMsg = ref('');
const mode = ref('json');
const createdProposal = ref(null);
const showPostCreateModal = ref(false);

// ── Prompt IA ──
const createPromptSubTab = ref('commercial');

const {
  promptText: createCommercialPromptText,
  isEditing: createCommercialPromptIsEditing,
  DEFAULT_PROMPT: createCommercialPromptDefault,
  loadSavedPrompt: loadCreateCommercialPrompt,
  savePrompt: saveCreateCommercialPrompt,
  resetPrompt: resetCreateCommercialPrompt,
  copyPrompt: copyCreateCommercialPrompt,
  downloadPrompt: createCommercialPromptDownload,
} = useSellerPrompt();

const createCommercialPromptEditBuffer = ref('');
const createCommercialPromptCopied = ref(false);

function startEditCreateCommercialPrompt() {
  createCommercialPromptEditBuffer.value = createCommercialPromptText.value;
  createCommercialPromptIsEditing.value = true;
}
function cancelEditCreateCommercialPrompt() {
  createCommercialPromptIsEditing.value = false;
}
function saveEditCreateCommercialPrompt() {
  saveCreateCommercialPrompt(createCommercialPromptEditBuffer.value);
  createCommercialPromptIsEditing.value = false;
}
async function handleCopyCreateCommercialPrompt() {
  await copyCreateCommercialPrompt();
  createCommercialPromptCopied.value = true;
  setTimeout(() => { createCommercialPromptCopied.value = false; }, 2000);
}
function handleResetCreateCommercialPrompt() {
  resetCreateCommercialPrompt();
  createCommercialPromptIsEditing.value = false;
}

const {
  promptText: createTechnicalPromptText,
  isEditing: createTechnicalPromptIsEditing,
  DEFAULT_PROMPT: createTechnicalPromptDefault,
  loadSavedPrompt: loadCreateTechnicalPrompt,
  savePrompt: saveCreateTechnicalPrompt,
  resetPrompt: resetCreateTechnicalPrompt,
  copyPrompt: copyCreateTechnicalPrompt,
  downloadPrompt: createTechnicalPromptDownload,
} = useTechnicalPrompt();

const createTechnicalPromptEditBuffer = ref('');
const createTechnicalPromptCopied = ref(false);

function startEditCreateTechnicalPrompt() {
  createTechnicalPromptEditBuffer.value = createTechnicalPromptText.value;
  createTechnicalPromptIsEditing.value = true;
}
function cancelEditCreateTechnicalPrompt() {
  createTechnicalPromptIsEditing.value = false;
}
function saveEditCreateTechnicalPrompt() {
  saveCreateTechnicalPrompt(createTechnicalPromptEditBuffer.value);
  createTechnicalPromptIsEditing.value = false;
}
async function handleCopyCreateTechnicalPrompt() {
  await copyCreateTechnicalPrompt();
  createTechnicalPromptCopied.value = true;
  setTimeout(() => { createTechnicalPromptCopied.value = false; }, 2000);
}
function handleResetCreateTechnicalPrompt() {
  resetCreateTechnicalPrompt();
  createTechnicalPromptIsEditing.value = false;
}

async function refreshCreateDefaults() {
  loadCreateCommercialPrompt();
  loadCreateTechnicalPrompt();
  await loadExpirationDefaults(form.language);
}

onMounted(refreshCreateDefaults);
usePanelRefresh(refreshCreateDefaults);

// -------------------------------------------------------------------------
// Shared helpers
// -------------------------------------------------------------------------
const DEFAULT_EXPIRATION_DAYS = 21;
const defaultExpirationDays = ref(DEFAULT_EXPIRATION_DAYS);
const pad = (n) => String(n).padStart(2, '0');

function buildDefaultExpiryStr(days = defaultExpirationDays.value) {
  const safeDays = Number.isInteger(days) && days > 0 ? days : DEFAULT_EXPIRATION_DAYS;
  const expiry = new Date(Date.now() + safeDays * 24 * 60 * 60 * 1000);
  return `${expiry.getFullYear()}-${pad(expiry.getMonth() + 1)}-${pad(expiry.getDate())}T${pad(expiry.getHours())}:${pad(expiry.getMinutes())}`;
}

function getExpiryDaysFromStr(datetimeStr) {
  if (!datetimeStr) return DEFAULT_EXPIRATION_DAYS;
  const diff = new Date(datetimeStr) - Date.now();
  return Math.max(1, Math.round(diff / (24 * 60 * 60 * 1000)));
}

const defaultExpiryStr = buildDefaultExpiryStr();
const expiryDaysInput = ref(getExpiryDaysFromStr(defaultExpiryStr));

// Updates both form.expires_at and jsonForm.expires_at regardless of active mode.
// This cross-mode sync is intentional: only one mode is visible at a time, and
// keeping both in sync avoids stale expiration dates when the user switches modes.
async function loadExpirationDefaults(lang = 'es') {
  const days = await proposalStore.fetchExpirationDays(lang, { force: true });
  if (!Number.isInteger(days) || days < 1) return;
  defaultExpirationDays.value = days;
  const expiryStr = buildDefaultExpiryStr(days);
  form.expires_at = expiryStr;
  jsonForm.expires_at = expiryStr;
}

function parseInvestmentString(str) {
  if (!str) return 0;
  if (typeof str === 'number') return str;
  const cleaned = String(str).replace(/[^0-9]/g, '');
  return cleaned ? Number(cleaned) : 0;
}

function formatError(errors) {
  if (errors && typeof errors === 'object') {
    return Object.entries(errors)
      .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
      .join(' | ');
  }
  return 'Error al crear la propuesta.';
}

// -------------------------------------------------------------------------
// MANUAL mode
// -------------------------------------------------------------------------
const form = reactive({
  title: '',
  client_id: null,
  client_name: '',
  client_email: '',
  client_phone: '',
  client_company: '',
  project_type: '',
  market_type: '',
  project_type_custom: '',
  market_type_custom: '',
  language: 'es',
  total_investment: 0,
  currency: 'COP',
  hosting_percent: 40,
  hosting_discount_semiannual: 20,
  hosting_discount_quarterly: 10,
  expires_at: defaultExpiryStr,
  reminder_days: 10,
  urgency_reminder_days: 15,
  discount_percent: 0,
});

function onClientSelected(client) {
  if (!client) return;
  form.client_id = client.id;
  form.client_name = client.name || form.client_name;
  form.client_email = client.is_email_placeholder ? '' : client.email || '';
  form.client_phone = client.phone || form.client_phone;
  form.client_company = client.company || form.client_company;
}

function onCreateInlineClient(typedName) {
  form.client_id = null;
  if (typedName) {
    form.client_name = typedName;
  }
}

const canSendDirectly = computed(() => {
  return !!(form.client_email && form.client_name && form.total_investment > 0);
});

async function handleSubmit() {
  errorMsg.value = '';

  const payload = { ...form };
  if (payload.expires_at) {
    payload.expires_at = new Date(payload.expires_at).toISOString();
  }

  const result = await proposalStore.createProposal(payload);
  if (result.success) {
    createdProposal.value = result.data;
    showPostCreateModal.value = true;
  } else {
    errorMsg.value = formatError(result.errors);
  }
}

async function handleCreateAndSend() {
  errorMsg.value = '';

  const payload = { ...form };
  if (payload.expires_at) {
    payload.expires_at = new Date(payload.expires_at).toISOString();
  }

  const result = await proposalStore.createProposal(payload);
  if (result.success) {
    await proposalStore.sendProposal(result.data.id);
    router.push(localePath(`/panel/proposals/${result.data.id}/edit`));
  } else {
    errorMsg.value = formatError(result.errors);
  }
}

async function handleSendCreated() {
  if (!createdProposal.value?.id) return;
  await proposalStore.sendProposal(createdProposal.value.id);
  router.push(localePath(`/panel/proposals/${createdProposal.value.id}/edit`));
}

// -------------------------------------------------------------------------
// JSON IMPORT mode
// -------------------------------------------------------------------------
const EXPECTED_SECTION_KEYS = [
  'general', 'executiveSummary', 'contextDiagnostic', 'conversionStrategy',
  'designUX', 'creativeSupport', 'developmentStages', 'processMethodology',
  'valueAddedModules', 'functionalRequirements', 'timeline', 'investment',
  'proposalSummary', 'finalNote', 'nextSteps', 'technicalDocument',
];

const jsonRaw = ref('');
const jsonParsed = ref(null);
const jsonError = ref('');
const jsonWarnings = ref([]);
const uploadedFileName = ref('');
const isDownloading = ref(false);
const templateCopied = ref(false);
const legacyFormatIssues = ref([]);

const jsonForm = reactive({
  title: '',
  client_email: 'usuario@temp.example.com',
  client_phone: '',
  project_type: '',
  market_type: '',
  project_type_custom: '',
  market_type_custom: '',
  language: 'es',
  total_investment: 0,
  currency: 'COP',
  hosting_percent: 40,
  hosting_discount_semiannual: 20,
  hosting_discount_quarterly: 10,
  expires_at: defaultExpiryStr,
  reminder_days: 10,
  urgency_reminder_days: 15,
  discount_percent: 0,
});

const jsonPreview = computed(() => {
  if (!jsonParsed.value) return {};
  const p = jsonParsed.value;
  const clientName = p.general?.clientName || '';
  const sectionCount = EXPECTED_SECTION_KEYS.filter((k) => k in p).length;
  const investment = p.investment?.totalInvestment || '';
  const epics = p.technicalDocument?.epics;
  const epicCount = Array.isArray(epics) ? epics.length : null;
  return { clientName, sectionCount, investment, epicCount };
});

watch(
  [() => form.language, () => jsonForm.language],
  ([langA, langB], [prevA, prevB]) => {
    const changed = langA !== prevA ? langA : langB !== prevB ? langB : null;
    if (changed) loadExpirationDefaults(changed);
  },
);

watch(() => form.expires_at, (val) => {
  expiryDaysInput.value = getExpiryDaysFromStr(val);
});

watch(() => jsonForm.expires_at, (val) => {
  expiryDaysInput.value = getExpiryDaysFromStr(val);
});

watch(expiryDaysInput, (days) => {
  const safeDays = Number.isInteger(days) && days > 0 ? days : DEFAULT_EXPIRATION_DAYS;
  const expiry = new Date(Date.now() + safeDays * 24 * 60 * 60 * 1000);
  const dateStr = `${expiry.getFullYear()}-${pad(expiry.getMonth() + 1)}-${pad(expiry.getDate())}`;
  const timeStr = form.expires_at ? form.expires_at.slice(11, 16) : `${pad(expiry.getHours())}:${pad(expiry.getMinutes())}`;
  const str = `${dateStr}T${timeStr}`;
  form.expires_at = str;
  jsonForm.expires_at = str;
});

function parseJson() {
  // Re-parses fired by every textarea keystroke must not clobber values
  // the user already edited in the metadata form.
  const isFirstParse = jsonParsed.value === null;

  jsonError.value = '';
  jsonParsed.value = null;
  legacyFormatIssues.value = [];

  const raw = jsonRaw.value.trim();
  if (!raw) return;

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    jsonError.value = 'JSON inválido. Revisa la sintaxis.';
    return;
  }

  if (typeof parsed !== 'object' || Array.isArray(parsed)) {
    jsonError.value = 'El JSON debe ser un objeto, no un array.';
    return;
  }

  if (!parsed.general || !parsed.general.clientName) {
    jsonError.value = 'El JSON debe incluir "general" con "clientName".';
    return;
  }

  legacyFormatIssues.value = detectLegacyTechnicalFormat(parsed).issues;

  jsonParsed.value = parsed;

  if (!isFirstParse) return;

  const clientName = parsed.general.clientName;
  const proposalTitle = parsed.general?.proposalTitle?.trim();
  jsonForm.title = proposalTitle || `Propuesta — ${clientName}`;
  jsonForm.total_investment = parseInvestmentString(parsed.investment?.totalInvestment);
  jsonForm.currency = parsed.investment?.currency || 'COP';

  const meta = parsed._meta?.optional_metadata || {};
  if (meta.client_email) jsonForm.client_email = meta.client_email;
  if (meta.client_phone) jsonForm.client_phone = meta.client_phone;
  if (meta.project_type) jsonForm.project_type = meta.project_type;
  if (meta.market_type) jsonForm.market_type = meta.market_type;
  if (meta.language) jsonForm.language = meta.language;
  if (meta.expires_at) {
    const d = new Date(meta.expires_at);
    if (!isNaN(d.getTime()) && d.getTime() > Date.now()) {
      jsonForm.expires_at = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }
  }
}

function handleFileUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  uploadedFileName.value = file.name;

  const reader = new FileReader();
  reader.onload = (e) => {
    jsonRaw.value = e.target.result;
    parseJson();
  };
  reader.readAsText(file);
}

async function copyTemplate() {
  try {
    const response = await get_request(`proposals/json-template/?lang=${jsonForm.language}`);
    const jsonStr = JSON.stringify(response.data, null, 2);
    await navigator.clipboard.writeText(jsonStr);
    templateCopied.value = true;
    setTimeout(() => { templateCopied.value = false; }, 2000);
  } catch (err) {
    console.error('Error copying template:', err);
  }
}

async function downloadTemplate() {
  isDownloading.value = true;
  try {
    const response = await get_request(`proposals/json-template/?lang=${jsonForm.language}`);
    const jsonStr = JSON.stringify(response.data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `proposal-template-${jsonForm.language}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('Error downloading template:', err);
  } finally {
    isDownloading.value = false;
  }
}

async function handleJsonSubmit() {
  errorMsg.value = '';

  if (!jsonParsed.value) {
    errorMsg.value = 'Pega o sube un JSON válido primero.';
    return;
  }

  const sections = { ...jsonParsed.value };
  delete sections._meta;

  const payload = {
    title: jsonForm.title,
    client_name: jsonParsed.value.general.clientName,
    client_email: jsonForm.client_email || '',
    client_phone: jsonForm.client_phone || '',
    project_type: jsonForm.project_type || '',
    market_type: jsonForm.market_type || '',
    project_type_custom: jsonForm.project_type_custom || '',
    market_type_custom: jsonForm.market_type_custom || '',
    language: jsonForm.language,
    total_investment: jsonForm.total_investment || 0,
    currency: jsonForm.currency,
    expires_at: jsonForm.expires_at ? new Date(jsonForm.expires_at).toISOString() : null,
    reminder_days: jsonForm.reminder_days,
    urgency_reminder_days: jsonForm.urgency_reminder_days,
    discount_percent: jsonForm.discount_percent,
    sections,
  };

  const result = await proposalStore.createProposalFromJSON(payload);
  if (result.success) {
    createdProposal.value = result.data;
    jsonWarnings.value = result.data?.warnings || [];
    showPostCreateModal.value = true;
  } else {
    errorMsg.value = formatError(result.errors);
  }
}
</script>
