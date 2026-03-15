<template>
  <div>
    <div class="mb-8">
      <NuxtLink :to="localePath('/panel/proposals')" class="text-sm text-gray-500 hover:text-gray-700 transition-colors">
        ← Volver a propuestas
      </NuxtLink>
      <h1 class="text-2xl font-light text-gray-900 mt-2">Nueva Propuesta</h1>
    </div>

    <!-- Tab toggle -->
    <div class="flex gap-1 mb-6 bg-gray-100 rounded-xl p-1 max-w-md">
      <button
        type="button"
        :class="[
          'flex-1 px-4 py-2 text-sm rounded-lg transition-all',
          mode === 'manual' ? 'bg-white shadow-sm font-medium text-gray-900' : 'text-gray-500 hover:text-gray-700'
        ]"
        @click="mode = 'manual'"
      >
        Manual
      </button>
      <button
        type="button"
        :class="[
          'flex-1 px-4 py-2 text-sm rounded-lg transition-all',
          mode === 'json' ? 'bg-white shadow-sm font-medium text-gray-900' : 'text-gray-500 hover:text-gray-700'
        ]"
        @click="mode = 'json'"
      >
        Importar JSON
      </button>
      <button
        type="button"
        :class="[
          'flex-1 px-4 py-2 text-sm rounded-lg transition-all',
          mode === 'prompt' ? 'bg-white shadow-sm font-medium text-gray-900' : 'text-gray-500 hover:text-gray-700'
        ]"
        @click="mode = 'prompt'"
      >
        Prompt IA
      </button>
    </div>

    <!-- ============================================================ -->
    <!-- MANUAL MODE (existing form, unchanged) -->
    <!-- ============================================================ -->
    <form v-if="mode === 'manual'" class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-8 max-w-2xl" @submit.prevent="handleSubmit">
      <div class="space-y-6">
        <!-- Title -->
        <div>
          <label for="create-title" class="block text-sm font-medium text-gray-700 mb-1">Título</label>
          <input
            id="create-title"
            v-model="form.title"
            type="text"
            required
            placeholder="Propuesta Desarrollo Web — Cliente"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
        </div>

        <!-- Client name -->
        <div>
          <label for="create-client-name" class="block text-sm font-medium text-gray-700 mb-1">Nombre del cliente</label>
          <input
            id="create-client-name"
            v-model="form.client_name"
            type="text"
            required
            placeholder="María García"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
        </div>

        <!-- Client email -->
        <div>
          <label for="create-client-email" class="block text-sm font-medium text-gray-700 mb-1">Email del cliente</label>
          <input
            id="create-client-email"
            v-model="form.client_email"
            type="email"
            placeholder="maria@example.com"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
        </div>

        <!-- Client phone -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Teléfono / WhatsApp</label>
          <input
            v-model="form.client_phone"
            type="tel"
            placeholder="+57 300 123 4567"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
        </div>

        <!-- Project type + Market type -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de proyecto</label>
            <select v-model="form.project_type" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white">
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
            <select v-model="form.market_type" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white">
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

        <!-- Language -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Idioma de la propuesta</label>
          <select
            v-model="form.language"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white"
          >
            <option value="es">Español</option>
            <option value="en">English</option>
          </select>
          <p class="text-xs text-gray-400 mt-1">Define los títulos e índices por defecto de las secciones.</p>
        </div>

        <!-- Investment + Currency -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Inversión total</label>
            <input
              v-model.number="form.total_investment"
              type="number"
              min="0"
              step="0.01"
              placeholder="3500000"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Moneda</label>
            <select
              v-model="form.currency"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white"
            >
              <option value="COP">COP</option>
              <option value="USD">USD</option>
            </select>
          </div>
        </div>

        <!-- Hosting percent -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Hosting (% de inversión total)</label>
          <div class="flex items-center gap-3">
            <input
              v-model.number="form.hosting_percent"
              type="number"
              min="0"
              max="100"
              class="w-32 px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
            <span class="text-sm text-gray-500">%</span>
            <span v-if="form.hosting_percent > 0 && form.total_investment > 0" class="text-sm text-blue-700 bg-blue-50 border border-blue-200 rounded-lg px-3 py-1.5">
              ☁️ ${{ Math.round(form.total_investment * form.hosting_percent / 100).toLocaleString() }} {{ form.currency }} / año
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-1">Se sincroniza con el % del Plan de Hosting en la sección "Tu inversión y cómo pagar".</p>
        </div>

        <!-- Expires at -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Fecha de expiración</label>
          <input
            v-model="form.expires_at"
            type="datetime-local"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
        </div>

        <!-- Reminder days -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Recordatorio (días después de enviar)</label>
            <input
              v-model.number="form.reminder_days"
              type="number"
              min="1"
              max="30"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
            <p class="text-xs text-gray-400 mt-1">Se enviará un email recordatorio al cliente X días después de enviar la propuesta.</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Urgencia (días después de enviar)</label>
            <input
              v-model.number="form.urgency_reminder_days"
              type="number"
              min="1"
              max="30"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
            <p class="text-xs text-gray-400 mt-1">Se enviará un email de urgencia X días después de enviar (incluye descuento si % > 0).</p>
          </div>
        </div>

        <!-- Discount -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descuento (%)</label>
          <input
            v-model.number="form.discount_percent"
            type="number"
            min="0"
            max="100"
            class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
          />
          <p class="text-xs text-gray-400 mt-1">Si es mayor a 0, se enviará un email de urgencia con descuento 2 días antes de expirar. 0 = sin descuento.</p>
        </div>

        <!-- Errors -->
        <div v-if="errorMsg" class="text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl">
          {{ errorMsg }}
        </div>

        <!-- Submit -->
        <div class="flex flex-wrap items-center gap-4 pt-2">
          <button
            type="submit"
            :disabled="proposalStore.isUpdating"
            class="px-5 sm:px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                   hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
          >
            {{ proposalStore.isUpdating ? 'Creando...' : 'Crear Propuesta' }}
          </button>
          <button
            v-if="canSendDirectly"
            type="button"
            :disabled="proposalStore.isUpdating"
            class="px-5 sm:px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm
                   hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50"
            @click="handleCreateAndSend"
          >
            {{ proposalStore.isUpdating ? 'Creando...' : 'Crear y Enviar' }}
          </button>
          <NuxtLink :to="localePath('/panel/proposals')" class="text-sm text-gray-500 hover:text-gray-700">
            Cancelar
          </NuxtLink>
        </div>
        <p v-if="canSendDirectly" class="text-xs text-gray-400 mt-2">Envía directamente si los datos del cliente están completos.</p>
      </div>
    </form>

    <!-- ============================================================ -->
    <!-- JSON IMPORT MODE -->
    <!-- ============================================================ -->
    <div v-else-if="mode === 'json'" class="max-w-3xl space-y-6">

      <!-- Download template row -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 class="text-sm font-medium text-gray-900">Plantilla JSON</h3>
            <p class="text-xs text-gray-400 mt-0.5">Descarga la plantilla con todas las secciones y campos de ejemplo.</p>
          </div>
          <div class="flex items-center gap-3">
            <select
              v-model="jsonForm.language"
              class="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            >
              <option value="es">Español</option>
              <option value="en">English</option>
            </select>
            <button
              type="button"
              :disabled="isDownloading"
              class="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm
                     font-medium hover:bg-gray-800 transition-colors disabled:opacity-50"
              @click="downloadTemplate"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {{ isDownloading ? 'Descargando...' : 'Descargar Plantilla' }}
            </button>
          </div>
        </div>
      </div>

      <!-- JSON input -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
        <h3 class="text-sm font-medium text-gray-900 mb-3">Pegar o subir JSON</h3>

        <div class="flex items-center gap-3 mb-3">
          <label
            class="inline-flex items-center gap-2 px-4 py-2 border border-gray-200 rounded-lg text-sm
                   text-gray-700 hover:bg-gray-50 cursor-pointer transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Subir archivo .json
            <input type="file" accept=".json" class="hidden" @change="handleFileUpload" />
          </label>
          <span v-if="uploadedFileName" class="text-xs text-gray-500">{{ uploadedFileName }}</span>
        </div>

        <textarea
          v-model="jsonRaw"
          rows="14"
          placeholder='{ "general": { "clientName": "..." }, "executiveSummary": { ... }, ... }'
          class="w-full px-4 py-3 border border-gray-200 rounded-xl text-xs font-mono leading-relaxed
                 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-y"
          @input="parseJson"
        ></textarea>

        <!-- Parse error -->
        <div v-if="jsonError" class="mt-2 text-sm text-red-600 bg-red-50 px-4 py-2 rounded-lg">
          {{ jsonError }}
        </div>

        <!-- Preview -->
        <div v-if="jsonParsed && !jsonError" class="mt-3 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3">
          <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span><span class="text-gray-500">Cliente:</span> <span class="font-medium text-gray-900">{{ jsonPreview.clientName }}</span></span>
            <span><span class="text-gray-500">Secciones:</span> <span class="font-medium text-gray-900">{{ jsonPreview.sectionCount }}</span></span>
            <span v-if="jsonPreview.investment"><span class="text-gray-500">Inversión:</span> <span class="font-medium text-gray-900">{{ jsonPreview.investment }}</span></span>
          </div>
        </div>
      </div>

      <!-- Metadata form -->
      <form v-if="jsonParsed && !jsonError" class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6" @submit.prevent="handleJsonSubmit">
        <h3 class="text-sm font-medium text-gray-900 mb-4">Datos de la propuesta</h3>
        <div class="space-y-4">
          <!-- Title -->
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Título</label>
            <input
              v-model="jsonForm.title"
              type="text"
              required
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>

          <!-- Client email -->
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Email del cliente</label>
            <input
              v-model="jsonForm.client_email"
              type="email"
              placeholder="cliente@example.com"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>

          <!-- Investment + Currency -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Inversión total</label>
              <input
                v-model.number="jsonForm.total_investment"
                type="number"
                min="0"
                step="0.01"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Moneda</label>
              <select
                v-model="jsonForm.currency"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none bg-white"
              >
                <option value="COP">COP</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>

          <!-- Project type / Market type -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Tipo de proyecto</label>
              <select v-model="jsonForm.project_type"
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
                v-if="jsonForm.project_type === 'other'"
                v-model="jsonForm.project_type_custom"
                type="text"
                placeholder="Especificar tipo de proyecto..."
                class="mt-2 w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Tipo de mercado</label>
              <select v-model="jsonForm.market_type"
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
                v-if="jsonForm.market_type === 'other'"
                v-model="jsonForm.market_type_custom"
                type="text"
                placeholder="Especificar tipo de mercado..."
                class="mt-2 w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
            </div>
          </div>

          <!-- Expires at -->
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">Fecha de expiración</label>
            <input
              v-model="jsonForm.expires_at"
              type="datetime-local"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                     focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
            />
          </div>

          <!-- Reminder / Urgency / Discount -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Recordatorio (día)</label>
              <input
                v-model.number="jsonForm.reminder_days"
                type="number" min="1" max="30"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Urgencia (día)</label>
              <input
                v-model.number="jsonForm.urgency_reminder_days"
                type="number" min="1" max="30"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Descuento (%)</label>
              <input
                v-model.number="jsonForm.discount_percent"
                type="number" min="0" max="100"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                       focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              />
            </div>
          </div>

          <!-- Errors -->
          <div v-if="errorMsg" class="text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl">
            {{ errorMsg }}
          </div>

          <!-- Submit -->
          <div class="flex flex-wrap items-center gap-4 pt-2">
            <button
              type="submit"
              :disabled="proposalStore.isUpdating"
              class="px-5 sm:px-6 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm
                     hover:bg-emerald-700 transition-colors shadow-sm disabled:opacity-50"
            >
              {{ proposalStore.isUpdating ? 'Creando...' : 'Crear desde JSON' }}
            </button>
            <NuxtLink :to="localePath('/panel/proposals')" class="text-sm text-gray-500 hover:text-gray-700">
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
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 sm:p-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <div>
            <h3 class="text-sm font-medium text-gray-900">Prompt para IA</h3>
            <p class="text-xs text-gray-400 mt-0.5">Copia este prompt y úsalo con ChatGPT, Claude u otra IA junto con el JSON plantilla para generar propuestas personalizadas.</p>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              @click="handleCopyCreatePrompt"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
              {{ createPromptCopied ? '¡Copiado!' : 'Copiar' }}
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              @click="createPromptDownload"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              Descargar .md
            </button>
          </div>
        </div>

        <div class="bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
          <div class="px-4 sm:px-6 py-4 max-h-[60vh] overflow-y-auto">
            <pre class="text-xs leading-relaxed text-gray-700 whitespace-pre-wrap font-mono break-words">{{ createPromptText }}</pre>
          </div>
        </div>

        <div class="mt-4 bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
          <p class="text-xs text-blue-700">
            <strong>Flujo recomendado:</strong> 1) Descarga la plantilla JSON desde la pestaña "Importar JSON" → 2) Copia este prompt → 3) Pega ambos en tu IA favorita → 4) Pega el JSON resultante de vuelta en "Importar JSON".
          </p>
        </div>
      </div>
    </div>

    <!-- Post-creation interstitial modal -->
    <teleport to="body">
      <div v-if="showPostCreateModal && createdProposal" class="fixed inset-0 z-[9990] flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-6 sm:p-8 text-center">
          <div class="text-5xl mb-4">✅</div>
          <h3 class="text-xl font-bold text-gray-900 mb-2">Propuesta creada</h3>
          <p class="text-sm text-gray-500 mb-4">{{ createdProposal.title }}</p>
          <div v-if="jsonWarnings.length" class="mb-4 text-left bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
            <p class="text-xs font-semibold text-amber-800 mb-1">⚠️ Advertencias del JSON</p>
            <p v-for="(warn, i) in jsonWarnings" :key="i" class="text-xs text-amber-700">{{ warn }}</p>
          </div>
          <div class="flex flex-col gap-3">
            <a
              :href="'/proposal/' + createdProposal.uuid + '?preview=1'"
              target="_blank"
              class="w-full px-5 py-2.5 bg-gray-100 text-gray-700 rounded-xl font-medium text-sm hover:bg-gray-200 transition-colors inline-flex items-center justify-center gap-2"
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
              class="w-full px-5 py-2.5 bg-emerald-600 text-white rounded-xl font-medium text-sm hover:bg-emerald-700 transition-colors"
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
import { reactive, ref, computed, onMounted } from 'vue';
import { get_request } from '~/stores/services/request_http';
import { useSellerPrompt } from '~/composables/useSellerPrompt';

const localePath = useLocalePath();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const router = useRouter();
const proposalStore = useProposalStore();
const errorMsg = ref('');
const mode = ref('manual');
const createdProposal = ref(null);
const showPostCreateModal = ref(false);

// ── Prompt IA ──
const {
  promptText: createPromptText,
  loadSavedPrompt: createLoadPrompt,
  copyPrompt: createCopyPrompt,
  downloadPrompt: createPromptDownload,
} = useSellerPrompt();

const createPromptCopied = ref(false);

async function handleCopyCreatePrompt() {
  await createCopyPrompt();
  createPromptCopied.value = true;
  setTimeout(() => { createPromptCopied.value = false; }, 2000);
}

onMounted(() => {
  createLoadPrompt();
});

// -------------------------------------------------------------------------
// Shared helpers
// -------------------------------------------------------------------------
const defaultExpiry = new Date(Date.now() + 20 * 24 * 60 * 60 * 1000);
const pad = (n) => String(n).padStart(2, '0');
const defaultExpiryStr = `${defaultExpiry.getFullYear()}-${pad(defaultExpiry.getMonth() + 1)}-${pad(defaultExpiry.getDate())}T${pad(defaultExpiry.getHours())}:${pad(defaultExpiry.getMinutes())}`;

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
  expires_at: defaultExpiryStr,
  reminder_days: 10,
  urgency_reminder_days: 15,
  discount_percent: 0,
});

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
  'designUX', 'creativeSupport', 'developmentStages', 'functionalRequirements',
  'timeline', 'investment', 'proposalSummary', 'finalNote', 'nextSteps',
];

const jsonRaw = ref('');
const jsonParsed = ref(null);
const jsonError = ref('');
const jsonWarnings = ref([]);
const uploadedFileName = ref('');
const isDownloading = ref(false);

const jsonForm = reactive({
  title: '',
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
  return { clientName, sectionCount, investment };
});

function parseJson() {
  jsonError.value = '';
  jsonParsed.value = null;

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

  jsonParsed.value = parsed;

  // Auto-populate metadata form
  const clientName = parsed.general.clientName;
  jsonForm.title = `Propuesta — ${clientName}`;
  jsonForm.total_investment = parseInvestmentString(parsed.investment?.totalInvestment);
  jsonForm.currency = parsed.investment?.currency || 'COP';

  // Auto-populate from _meta.optional_metadata if present
  const meta = parsed._meta?.optional_metadata || {};
  if (meta.client_email) jsonForm.client_email = meta.client_email;
  if (meta.client_phone) jsonForm.client_phone = meta.client_phone;
  if (meta.project_type) jsonForm.project_type = meta.project_type;
  if (meta.market_type) jsonForm.market_type = meta.market_type;
  if (meta.language) jsonForm.language = meta.language;
  if (meta.expires_at) {
    const d = new Date(meta.expires_at);
    if (!isNaN(d.getTime())) {
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
