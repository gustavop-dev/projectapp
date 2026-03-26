<template>
  <div id="platform-changes">
    <!-- Loading -->
    <div v-if="crStore.isLoading && !crStore.changeRequests.length" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <template v-else>
      <!-- Header -->
      <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between" data-enter>
        <div>
          <NuxtLink :to="localePath('/platform/changes')" class="mb-2 inline-flex items-center gap-1.5 text-sm text-green-light transition hover:text-esmerald dark:hover:text-white">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
            Solicitudes
          </NuxtLink>
          <h1 class="text-xl font-bold text-esmerald dark:text-white sm:text-2xl">Solicitudes de cambio</h1>
        </div>

        <div class="flex items-center gap-3">
          <!-- Stats pills -->
          <div class="hidden items-center gap-2 sm:flex">
            <span class="rounded-full bg-amber-500/15 px-2.5 py-1 text-[10px] font-semibold text-amber-600 dark:text-amber-400">
              {{ crStore.pendingCount }} pendientes
            </span>
            <span class="rounded-full bg-blue-500/15 px-2.5 py-1 text-[10px] font-semibold text-blue-600 dark:text-blue-400">
              {{ crStore.evaluatingCount }} en evaluación
            </span>
          </div>

          <!-- Create button -->
          <button
            type="button"
            class="flex items-center gap-1.5 rounded-xl bg-lemon px-4 py-2 text-sm font-semibold text-esmerald-dark transition hover:brightness-105"
            @click="openCreateModal"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
            Nueva solicitud
          </button>
        </div>
      </div>

      <!-- Status filter tabs -->
      <div class="mb-5 flex gap-1.5 overflow-x-auto pb-1" data-enter>
        <button
          v-for="tab in statusTabs"
          :key="tab.value"
          type="button"
          class="shrink-0 rounded-full px-3.5 py-1.5 text-xs font-medium transition"
          :class="activeFilter === tab.value
            ? 'bg-esmerald text-white dark:bg-lemon dark:text-esmerald-dark'
            : 'text-green-light hover:bg-esmerald-light/50 dark:hover:bg-white/[0.06]'"
          @click="activeFilter = tab.value"
        >
          {{ tab.label }}
          <span v-if="tab.count !== undefined" class="ml-1 opacity-60">{{ tab.count }}</span>
        </button>
      </div>

      <!-- List -->
      <div v-if="filteredRequests.length" class="space-y-3" data-enter>
        <div
          v-for="cr in filteredRequests"
          :key="cr.id"
          class="group cursor-pointer rounded-2xl border border-esmerald/[0.06] bg-white p-5 transition hover:border-esmerald/15 hover:shadow-md dark:border-white/[0.06] dark:bg-esmerald dark:hover:border-white/12"
          @click="openDetailModal(cr)"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1">
              <div class="mb-2 flex flex-wrap items-center gap-2">
                <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase" :class="statusBadgeClass(cr.status)">
                  {{ statusLabel(cr.status) }}
                </span>
                <span class="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase" :class="priorityBadgeClass(cr.suggested_priority)">
                  {{ priorityLabel(cr.suggested_priority) }}
                </span>
                <span v-if="cr.is_urgent" class="rounded-full bg-red-500/15 px-2 py-0.5 text-[10px] font-bold uppercase text-red-600 dark:text-red-400">
                  Urgente
                </span>
                <span v-if="cr.linked_requirement_id" class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                  Convertida
                </span>
              </div>
              <h3 class="text-sm font-semibold text-esmerald dark:text-white">{{ cr.title }}</h3>
              <p v-if="cr.description" class="mt-1 line-clamp-2 text-xs leading-relaxed text-green-light">{{ cr.description }}</p>
            </div>
            <svg class="h-4 w-4 shrink-0 text-green-light/30 transition group-hover:text-esmerald dark:group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
          </div>

          <div class="mt-3 flex items-center gap-4 text-[10px] text-green-light/60">
            <span v-if="cr.module_or_screen">{{ cr.module_or_screen }}</span>
            <span>{{ cr.created_by_name }}</span>
            <span>{{ formatDate(cr.created_at) }}</span>
            <span v-if="cr.comments_count" class="flex items-center gap-1">
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
              {{ cr.comments_count }}
            </span>
            <span v-if="cr.estimated_time" class="flex items-center gap-1">
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke-width="1.5" /><path d="M12 6v6l4 2" stroke-width="1.5" /></svg>
              {{ cr.estimated_time }}
            </span>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="py-16 text-center" data-enter>
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-esmerald-light/50 dark:bg-white/[0.04]">
          <svg class="h-8 w-8 text-green-light/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
        </div>
        <p class="text-sm text-green-light">
          {{ activeFilter === 'all' ? 'No hay solicitudes de cambio aún.' : 'No hay solicitudes con este estado.' }}
        </p>
        <button
          type="button"
          class="mt-4 rounded-xl bg-lemon px-5 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105"
          @click="openCreateModal"
        >
          Crear primera solicitud
        </button>
      </div>
    </template>

    <!-- Create modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div
          v-if="isCreateOpen"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm"
          @click.self="isCreateOpen = false"
        >
          <Transition name="modal-content" appear>
            <div v-if="isCreateOpen" class="w-full max-w-md rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <h2 class="mb-5 text-lg font-bold text-esmerald dark:text-white">Nueva solicitud de cambio</h2>

              <form class="space-y-4" @submit.prevent="handleCreate">
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Título <span class="text-red-400">*</span></label>
                  <input v-model="createForm.title" type="text" required placeholder="¿Qué cambio necesitas?" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Descripción</label>
                  <textarea v-model="createForm.description" rows="3" placeholder="Describe el cambio con el mayor detalle posible..." class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Módulo / Pantalla</label>
                    <input v-model="createForm.module_or_screen" type="text" placeholder="Ej: Catálogo" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Prioridad sugerida</label>
                    <select v-model="createForm.suggested_priority" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                      <option value="low">Baja</option>
                      <option value="medium">Media</option>
                      <option value="high">Alta</option>
                      <option value="critical">Crítica</option>
                    </select>
                  </div>
                </div>
                <label class="flex items-center gap-2 text-xs text-green-light">
                  <input v-model="createForm.is_urgent" type="checkbox" class="rounded border-esmerald/20 dark:border-white/20" />
                  Marcar como urgente
                </label>

                <!-- Screenshot upload -->
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Pantallazo (opcional)</label>
                  <div
                    class="relative flex min-h-[80px] cursor-pointer items-center justify-center rounded-xl border-2 border-dashed border-esmerald/15 bg-esmerald-light/20 transition hover:border-esmerald/30 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-white/20"
                    @click="$refs.screenshotInput.click()"
                    @dragover.prevent
                    @drop.prevent="handleScreenshotDrop"
                  >
                    <input ref="screenshotInput" type="file" accept="image/*" class="hidden" @change="handleScreenshotSelect" />
                    <div v-if="!screenshotPreview" class="py-4 text-center">
                      <svg class="mx-auto mb-1.5 h-6 w-6 text-green-light/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                      <p class="text-[11px] text-green-light/50">Arrastra o haz clic para subir</p>
                    </div>
                    <div v-else class="relative w-full p-2">
                      <img :src="screenshotPreview" alt="Preview" class="mx-auto max-h-32 rounded-lg object-contain" />
                      <button type="button" class="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-black/50 text-white transition hover:bg-black/70" @click.stop="removeScreenshot">
                        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                      </button>
                    </div>
                  </div>
                </div>

                <div class="flex justify-end gap-3 pt-2">
                  <button type="button" class="rounded-xl border border-esmerald/10 px-5 py-2.5 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white" @click="isCreateOpen = false">Cancelar</button>
                  <button type="submit" :disabled="!createForm.title.trim() || crStore.isUpdating" class="rounded-xl bg-lemon px-6 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50">
                    {{ crStore.isUpdating ? 'Creando...' : 'Crear solicitud' }}
                  </button>
                </div>
              </form>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- Detail modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div
          v-if="detailCR"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm"
          @click.self="detailCR = null"
        >
          <Transition name="modal-content" appear>
            <div v-if="detailCR" class="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <!-- Header -->
              <div class="mb-5 flex items-start justify-between gap-4">
                <div class="flex-1">
                  <div class="mb-2 flex flex-wrap items-center gap-2">
                    <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase" :class="statusBadgeClass(detailCR.status)">{{ statusLabel(detailCR.status) }}</span>
                    <span class="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase" :class="priorityBadgeClass(detailCR.suggested_priority)">{{ priorityLabel(detailCR.suggested_priority) }}</span>
                    <span v-if="detailCR.is_urgent" class="rounded-full bg-red-500/15 px-2 py-0.5 text-[10px] font-bold uppercase text-red-600 dark:text-red-400">Urgente</span>
                  </div>
                  <h2 class="text-lg font-bold text-esmerald dark:text-white">{{ detailCR.title }}</h2>
                </div>
                <button type="button" class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white" @click="detailCR = null">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              <!-- Description -->
              <div v-if="detailCR.description" class="mb-5 rounded-xl border border-esmerald/[0.04] bg-esmerald-light/20 p-4 text-sm leading-relaxed text-green-light dark:border-white/[0.04] dark:bg-white/[0.02]">
                {{ detailCR.description }}
              </div>

              <!-- Screenshot -->
              <div v-if="detailCR.screenshot_url" class="mb-5">
                <a :href="detailCR.screenshot_url" target="_blank" class="block overflow-hidden rounded-xl border border-esmerald/[0.06] transition hover:border-esmerald/20 dark:border-white/[0.06] dark:hover:border-white/15">
                  <img :src="detailCR.screenshot_url" alt="Pantallazo" class="w-full object-contain" style="max-height: 300px" />
                </a>
              </div>

              <!-- Meta -->
              <div class="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Módulo</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ detailCR.module_or_screen || '—' }}</p>
                </div>
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Solicitado por</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ detailCR.created_by_name }}</p>
                </div>
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Fecha</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ formatDate(detailCR.created_at) }}</p>
                </div>
              </div>

              <!-- Admin response -->
              <div v-if="detailCR.admin_response" class="mb-5 rounded-xl border-l-2 border-l-esmerald/30 bg-esmerald-light/20 p-4 dark:border-l-lemon/40 dark:bg-white/[0.02]">
                <p class="mb-1 text-[10px] font-semibold uppercase tracking-wider text-esmerald/60 dark:text-lemon/60">Respuesta del equipo</p>
                <p class="text-sm leading-relaxed text-green-light">{{ detailCR.admin_response }}</p>
                <div v-if="detailCR.estimated_time || detailCR.estimated_cost" class="mt-3 flex flex-wrap gap-3">
                  <span v-if="detailCR.estimated_time" class="flex items-center gap-1 rounded-full bg-esmerald/[0.06] px-2.5 py-1 text-[10px] font-semibold text-esmerald dark:bg-white/[0.06] dark:text-white">
                    <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke-width="1.5" /><path d="M12 6v6l4 2" stroke-width="1.5" /></svg>
                    {{ detailCR.estimated_time }}
                  </span>
                  <span v-if="detailCR.estimated_cost !== null && detailCR.estimated_cost !== undefined" class="flex items-center gap-1 rounded-full bg-esmerald/[0.06] px-2.5 py-1 text-[10px] font-semibold text-esmerald dark:bg-white/[0.06] dark:text-white">
                    ${{ Number(detailCR.estimated_cost).toLocaleString('es-CO') }}
                  </span>
                </div>
              </div>

              <!-- Linked requirement -->
              <div v-if="detailCR.linked_requirement_id" class="mb-5 flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
                <svg class="h-4 w-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <span class="text-xs font-medium text-emerald-600 dark:text-emerald-400">Convertida en requerimiento #{{ detailCR.linked_requirement_id }}</span>
              </div>

              <!-- Admin actions -->
              <div v-if="authStore.isAdmin" class="mb-5 space-y-3">
                <!-- Evaluate form -->
                <div v-if="showEvaluateForm" class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
                  <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">Evaluar solicitud</p>
                  <div class="space-y-3">
                    <div>
                      <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Estado</label>
                      <select v-model="evalForm.status" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-2.5 text-sm text-esmerald outline-none focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                        <option value="pending">Pendiente</option>
                        <option value="evaluating">En evaluación</option>
                        <option value="approved">Aprobada</option>
                        <option value="rejected">Rechazada</option>
                        <option value="needs_clarification">Requiere aclaración</option>
                        <option value="out_of_scope">Fuera de alcance</option>
                      </select>
                    </div>
                    <div>
                      <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Respuesta</label>
                      <textarea v-model="evalForm.admin_response" rows="2" placeholder="Respuesta para el cliente..." class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-2.5 text-sm text-esmerald outline-none placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                      <div>
                        <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Tiempo estimado</label>
                        <input v-model="evalForm.estimated_time" type="text" placeholder="Ej: 2 semanas" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-2.5 text-sm text-esmerald outline-none placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                      </div>
                      <div>
                        <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Costo estimado</label>
                        <input v-model.number="evalForm.estimated_cost" type="number" min="0" step="1000" placeholder="0" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-2.5 text-sm text-esmerald outline-none placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                      </div>
                    </div>
                    <div class="flex justify-end gap-2">
                      <button type="button" class="rounded-lg px-3 py-1.5 text-xs text-green-light hover:text-esmerald dark:hover:text-white" @click="showEvaluateForm = false">Cancelar</button>
                      <button type="button" :disabled="crStore.isUpdating" class="rounded-lg bg-esmerald px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-esmerald/90 disabled:opacity-50 dark:bg-lemon dark:text-esmerald-dark" @click="handleEvaluate">
                        {{ crStore.isUpdating ? 'Guardando...' : 'Guardar evaluación' }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Action buttons -->
                <div v-else class="flex flex-wrap gap-2">
                  <button
                    type="button"
                    class="rounded-xl border border-esmerald/10 px-4 py-2 text-xs font-medium text-esmerald transition hover:bg-esmerald-light dark:border-white/10 dark:text-white dark:hover:bg-white/[0.06]"
                    @click="openEvaluateForm"
                  >
                    Evaluar
                  </button>
                  <button
                    v-if="detailCR.status === 'approved' && !detailCR.linked_requirement_id"
                    type="button"
                    :disabled="crStore.isUpdating"
                    class="rounded-xl bg-emerald-500 px-4 py-2 text-xs font-semibold text-white transition hover:bg-emerald-600 disabled:opacity-50"
                    @click="handleConvert"
                  >
                    Convertir en requerimiento
                  </button>
                  <button
                    type="button"
                    class="rounded-xl border border-red-200 px-4 py-2 text-xs font-medium text-red-500 transition hover:bg-red-50 dark:border-red-500/20 dark:hover:bg-red-500/10"
                    @click="handleDelete"
                  >
                    Eliminar
                  </button>
                </div>
              </div>

              <!-- Comments -->
              <div class="mb-4">
                <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">
                  Comentarios{{ detailCR.comments ? ` (${detailCR.comments.length})` : '' }}
                </p>

                <div v-if="detailCR.comments && detailCR.comments.length" class="mb-4 space-y-3">
                  <div
                    v-for="comment in detailCR.comments"
                    :key="comment.id"
                    class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]"
                    :class="comment.is_internal ? 'border-l-2 border-l-amber-400' : ''"
                  >
                    <div class="mb-1 flex items-center justify-between">
                      <span class="text-xs font-medium text-esmerald dark:text-white">{{ comment.user_name }}</span>
                      <span class="text-[10px] text-green-light/40">{{ formatDate(comment.created_at) }}</span>
                    </div>
                    <p class="text-sm leading-relaxed text-green-light">{{ comment.content }}</p>
                    <span v-if="comment.is_internal" class="mt-1 inline-block text-[9px] font-semibold uppercase tracking-wider text-amber-500">Interno</span>
                  </div>
                </div>

                <!-- Add comment -->
                <form class="flex gap-2" @submit.prevent="handleAddComment">
                  <input
                    v-model="newComment"
                    type="text"
                    placeholder="Escribe un comentario..."
                    class="flex-1 rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-2.5 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40"
                  />
                  <button
                    type="submit"
                    :disabled="!newComment.trim()"
                    class="rounded-xl bg-esmerald px-4 py-2.5 text-sm font-medium text-white transition hover:bg-esmerald/90 disabled:opacity-40 dark:bg-lemon dark:text-esmerald-dark"
                  >
                    Enviar
                  </button>
                </form>
                <label v-if="authStore.isAdmin" class="mt-2 flex items-center gap-2 text-xs text-green-light/60">
                  <input v-model="commentInternal" type="checkbox" class="rounded border-esmerald/20 dark:border-white/20" />
                  Comentario interno (solo admins)
                </label>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformChangeRequestsStore } from '~/stores/platform-change-requests'
import { usePlatformProjectsStore } from '~/stores/platform-projects'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

useHead({ title: 'Solicitudes de cambio — ProjectApp' })
usePageEntrance('#platform-changes')

const route = useRoute()
const localePath = useLocalePath()
const authStore = usePlatformAuthStore()
const crStore = usePlatformChangeRequestsStore()
const projectsStore = usePlatformProjectsStore()

const projectId = computed(() => route.params.id)
const projectName = computed(() => projectsStore.currentProject?.name || 'Proyecto')

const activeFilter = ref('all')

const statusTabs = computed(() => [
  { value: 'all', label: 'Todas', count: crStore.changeRequests.length },
  { value: 'pending', label: 'Pendientes', count: crStore.pendingCount },
  { value: 'evaluating', label: 'En evaluación', count: crStore.evaluatingCount },
  { value: 'approved', label: 'Aprobadas', count: crStore.approvedCount },
  { value: 'rejected', label: 'Rechazadas', count: crStore.rejectedCount },
  { value: 'needs_clarification', label: 'Requiere aclaración' },
  { value: 'out_of_scope', label: 'Fuera de alcance' },
])

const filteredRequests = computed(() => crStore.filteredByStatus(activeFilter.value))

const isCreateOpen = ref(false)
const createForm = reactive({
  title: '',
  description: '',
  module_or_screen: '',
  suggested_priority: 'medium',
  is_urgent: false,
})

const screenshotFile = ref(null)
const screenshotPreview = ref(null)

const detailCR = ref(null)
const newComment = ref('')
const commentInternal = ref(false)
const showEvaluateForm = ref(false)
const evalForm = reactive({
  status: 'evaluating',
  admin_response: '',
  estimated_time: '',
  estimated_cost: null,
})

function statusBadgeClass(s) {
  const map = {
    pending: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    evaluating: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    approved: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    rejected: 'bg-red-500/15 text-red-600 dark:text-red-400',
    needs_clarification: 'bg-purple-500/15 text-purple-600 dark:text-purple-400',
    out_of_scope: 'bg-gray-500/15 text-gray-500',
  }
  return map[s] || map.pending
}

function statusLabel(s) {
  const map = {
    pending: 'Pendiente',
    evaluating: 'En evaluación',
    approved: 'Aprobada',
    rejected: 'Rechazada',
    needs_clarification: 'Requiere aclaración',
    out_of_scope: 'Fuera de alcance',
  }
  return map[s] || s
}

function priorityBadgeClass(p) {
  const map = {
    critical: 'bg-red-500/15 text-red-600 dark:text-red-400',
    high: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    medium: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    low: 'bg-gray-500/15 text-gray-500',
  }
  return map[p] || map.medium
}

function priorityLabel(p) {
  const map = { critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja' }
  return map[p] || p
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })
}

function openCreateModal() {
  createForm.title = ''
  createForm.description = ''
  createForm.module_or_screen = ''
  createForm.suggested_priority = 'medium'
  createForm.is_urgent = false
  screenshotFile.value = null
  screenshotPreview.value = null
  isCreateOpen.value = true
}

function handleScreenshotSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return
  setScreenshot(file)
}

function handleScreenshotDrop(event) {
  const file = event.dataTransfer.files?.[0]
  if (!file || !file.type.startsWith('image/')) return
  setScreenshot(file)
}

function setScreenshot(file) {
  screenshotFile.value = file
  screenshotPreview.value = URL.createObjectURL(file)
}

function removeScreenshot() {
  screenshotFile.value = null
  if (screenshotPreview.value) URL.revokeObjectURL(screenshotPreview.value)
  screenshotPreview.value = null
}

async function handleCreate() {
  if (!createForm.title.trim()) return
  let payload
  if (screenshotFile.value) {
    payload = new FormData()
    payload.append('title', createForm.title)
    payload.append('description', createForm.description)
    payload.append('module_or_screen', createForm.module_or_screen)
    payload.append('suggested_priority', createForm.suggested_priority)
    payload.append('is_urgent', createForm.is_urgent)
    payload.append('screenshot', screenshotFile.value)
  } else {
    payload = { ...createForm }
  }
  const result = await crStore.createChangeRequest(projectId.value, payload)
  if (result.success) {
    if (screenshotPreview.value) URL.revokeObjectURL(screenshotPreview.value)
    isCreateOpen.value = false
  }
}

async function openDetailModal(cr) {
  detailCR.value = cr
  newComment.value = ''
  commentInternal.value = false
  showEvaluateForm.value = false
  const result = await crStore.fetchChangeRequest(projectId.value, cr.id)
  if (result.success) detailCR.value = result.data
}

function openEvaluateForm() {
  evalForm.status = detailCR.value?.status || 'evaluating'
  evalForm.admin_response = detailCR.value?.admin_response || ''
  evalForm.estimated_time = detailCR.value?.estimated_time || ''
  evalForm.estimated_cost = detailCR.value?.estimated_cost || null
  showEvaluateForm.value = true
}

async function handleEvaluate() {
  if (!detailCR.value) return
  const payload = { ...evalForm }
  if (!payload.estimated_cost) payload.estimated_cost = null
  const result = await crStore.evaluateChangeRequest(projectId.value, detailCR.value.id, payload)
  if (result.success) {
    detailCR.value = result.data
    showEvaluateForm.value = false
  }
}

async function handleConvert() {
  if (!detailCR.value) return
  const result = await crStore.convertToRequirement(projectId.value, detailCR.value.id)
  if (result.success) {
    detailCR.value = result.data
  }
}

async function handleDelete() {
  if (!detailCR.value) return
  const result = await crStore.deleteChangeRequest(projectId.value, detailCR.value.id)
  if (result.success) {
    detailCR.value = null
  }
}

async function handleAddComment() {
  if (!newComment.value.trim() || !detailCR.value) return
  const result = await crStore.addComment(projectId.value, detailCR.value.id, newComment.value.trim(), commentInternal.value)
  if (result.success) {
    newComment.value = ''
    commentInternal.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    crStore.fetchChangeRequests(projectId.value),
    projectsStore.currentProject?.id !== Number(projectId.value)
      ? projectsStore.fetchProject(projectId.value)
      : Promise.resolve(),
  ])
})
</script>

<style scoped>
.modal-overlay-enter-active,
.modal-overlay-leave-active { transition: opacity 0.25s ease; }
.modal-overlay-enter-from,
.modal-overlay-leave-to { opacity: 0; }
.modal-content-enter-active { transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-content-leave-active { transition: all 0.2s ease-in; }
.modal-content-enter-from { opacity: 0; transform: scale(0.95) translateY(10px); }
.modal-content-leave-to { opacity: 0; transform: scale(0.97); }
</style>
