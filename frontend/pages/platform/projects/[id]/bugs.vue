<template>
  <div id="platform-bugs">
    <!-- Loading -->
    <div v-if="bugStore.isLoading && !bugStore.bugReports.length" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <template v-else>
      <!-- Header -->
      <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between" data-enter>
        <div>
          <NuxtLink :to="localePath('/platform/bugs')" class="mb-2 inline-flex items-center gap-1.5 text-sm text-green-light transition hover:text-esmerald dark:hover:text-white">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
            Bugs
          </NuxtLink>
          <h1 class="text-xl font-bold text-esmerald dark:text-white sm:text-2xl">Reporte de bugs</h1>
        </div>

        <div class="flex items-center gap-3">
          <div class="hidden items-center gap-2 sm:flex">
            <span class="rounded-full bg-red-500/15 px-2.5 py-1 text-[10px] font-semibold text-red-600 dark:text-red-400">
              {{ bugStore.reportedCount }} reportados
            </span>
            <span class="rounded-full bg-amber-500/15 px-2.5 py-1 text-[10px] font-semibold text-amber-600 dark:text-amber-400">
              {{ bugStore.fixingCount }} en corrección
            </span>
          </div>

          <button
            type="button"
            class="flex items-center gap-1.5 rounded-xl bg-lemon px-4 py-2 text-sm font-semibold text-esmerald-dark transition hover:brightness-105"
            @click="openCreateModal"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
            Reportar bug
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
      <div v-if="filteredBugs.length" class="space-y-3" data-enter>
        <div
          v-for="bug in filteredBugs"
          :key="bug.id"
          class="group cursor-pointer rounded-2xl border border-esmerald/[0.06] bg-white p-5 transition hover:border-esmerald/15 hover:shadow-md dark:border-white/[0.06] dark:bg-esmerald dark:hover:border-white/12"
          @click="openDetailModal(bug)"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1">
              <div class="mb-2 flex flex-wrap items-center gap-2">
                <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase" :class="statusBadgeClass(bug.status)">
                  {{ statusLabel(bug.status) }}
                </span>
                <span class="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase" :class="severityBadgeClass(bug.severity)">
                  {{ severityLabel(bug.severity) }}
                </span>
                <span v-if="bug.is_recurring" class="rounded-full bg-purple-500/15 px-2 py-0.5 text-[10px] font-bold uppercase text-purple-600 dark:text-purple-400">
                  Recurrente
                </span>
                <span v-if="bug.screenshot_url" class="text-green-light/30">
                  <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                </span>
              </div>
              <h3 class="text-sm font-semibold text-esmerald dark:text-white">{{ bug.title }}</h3>
              <p v-if="bug.description" class="mt-1 line-clamp-2 text-xs leading-relaxed text-green-light">{{ bug.description }}</p>
            </div>
            <svg class="h-4 w-4 shrink-0 text-green-light/30 transition group-hover:text-esmerald dark:group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
          </div>

          <div class="mt-3 flex items-center gap-4 text-[10px] text-green-light/60">
            <span>{{ envLabel(bug.environment) }}</span>
            <span v-if="bug.device_browser">{{ bug.device_browser }}</span>
            <span>{{ bug.reported_by_name }}</span>
            <span>{{ formatDate(bug.created_at) }}</span>
            <span v-if="bug.comments_count" class="flex items-center gap-1">
              <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
              {{ bug.comments_count }}
            </span>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else class="py-16 text-center" data-enter>
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-esmerald-light/50 dark:bg-white/[0.04]">
          <svg class="h-8 w-8 text-green-light/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
        </div>
        <p class="text-sm text-green-light">
          {{ activeFilter === 'all' ? 'No hay bugs reportados aún.' : 'No hay bugs con este estado.' }}
        </p>
        <button type="button" class="mt-4 rounded-xl bg-lemon px-5 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105" @click="openCreateModal">
          Reportar primer bug
        </button>
      </div>
    </template>

    <!-- Create modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div v-if="isCreateOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm" @click.self="isCreateOpen = false">
          <Transition name="modal-content" appear>
            <div v-if="isCreateOpen" class="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <h2 class="mb-5 text-lg font-bold text-esmerald dark:text-white">Reportar bug</h2>

              <form class="space-y-4" @submit.prevent="handleCreate">
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Título <span class="text-red-400">*</span></label>
                  <input v-model="createForm.title" type="text" required placeholder="¿Qué está fallando?" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Descripción</label>
                  <textarea v-model="createForm.description" rows="2" placeholder="Describe el error con detalle..." class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>

                <!-- Steps to reproduce -->
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Pasos para reproducir</label>
                  <div class="space-y-2">
                    <div v-for="(step, i) in createForm.steps_to_reproduce" :key="i" class="flex items-center gap-2">
                      <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-esmerald/[0.06] text-[10px] font-bold text-green-light dark:bg-white/[0.06]">{{ i + 1 }}</span>
                      <input v-model="createForm.steps_to_reproduce[i]" type="text" :placeholder="`Paso ${i + 1}`" class="flex-1 rounded-lg border border-esmerald/10 bg-esmerald-light/40 px-3 py-2 text-sm text-esmerald outline-none placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                      <button v-if="createForm.steps_to_reproduce.length > 1" type="button" class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-green-light/40 hover:text-red-400" @click="createForm.steps_to_reproduce.splice(i, 1)">
                        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                      </button>
                    </div>
                    <button type="button" class="text-xs font-medium text-esmerald/60 transition hover:text-esmerald dark:text-white/60 dark:hover:text-white" @click="createForm.steps_to_reproduce.push('')">
                      + Agregar paso
                    </button>
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Comportamiento esperado</label>
                    <textarea v-model="createForm.expected_behavior" rows="2" placeholder="¿Qué debería pasar?" class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-3 py-2.5 text-sm text-esmerald outline-none placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Comportamiento actual</label>
                    <textarea v-model="createForm.actual_behavior" rows="2" placeholder="¿Qué pasa realmente?" class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-3 py-2.5 text-sm text-esmerald outline-none placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                  </div>
                </div>

                <div class="grid grid-cols-3 gap-3">
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Severidad</label>
                    <select v-model="createForm.severity" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-3 py-2.5 text-sm text-esmerald outline-none focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                      <option value="low">Baja</option>
                      <option value="medium">Media</option>
                      <option value="high">Alta</option>
                      <option value="critical">Crítica</option>
                    </select>
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Entorno</label>
                    <select v-model="createForm.environment" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-3 py-2.5 text-sm text-esmerald outline-none focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                      <option value="production">Producción</option>
                      <option value="staging">Staging</option>
                      <option value="dev">Desarrollo</option>
                    </select>
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Navegador</label>
                    <input v-model="createForm.device_browser" type="text" placeholder="Chrome / iOS" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-3 py-2.5 text-sm text-esmerald outline-none placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                  </div>
                </div>

                <label class="flex items-center gap-2 text-xs text-green-light">
                  <input v-model="createForm.is_recurring" type="checkbox" class="rounded border-esmerald/20 dark:border-white/20" />
                  Es un error recurrente
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
                  <button type="submit" :disabled="!createForm.title.trim() || bugStore.isUpdating" class="rounded-xl bg-lemon px-6 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50">
                    {{ bugStore.isUpdating ? 'Reportando...' : 'Reportar bug' }}
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
        <div v-if="detailBug" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm" @click.self="detailBug = null">
          <Transition name="modal-content" appear>
            <div v-if="detailBug" class="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <!-- Header -->
              <div class="mb-5 flex items-start justify-between gap-4">
                <div class="flex-1">
                  <div class="mb-2 flex flex-wrap items-center gap-2">
                    <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase" :class="statusBadgeClass(detailBug.status)">{{ statusLabel(detailBug.status) }}</span>
                    <span class="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase" :class="severityBadgeClass(detailBug.severity)">{{ severityLabel(detailBug.severity) }}</span>
                    <span v-if="detailBug.is_recurring" class="rounded-full bg-purple-500/15 px-2 py-0.5 text-[10px] font-bold uppercase text-purple-600 dark:text-purple-400">Recurrente</span>
                  </div>
                  <h2 class="text-lg font-bold text-esmerald dark:text-white">{{ detailBug.title }}</h2>
                </div>
                <button type="button" class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white" @click="detailBug = null">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              <!-- Description -->
              <div v-if="detailBug.description" class="mb-5 rounded-xl border border-esmerald/[0.04] bg-esmerald-light/20 p-4 text-sm leading-relaxed text-green-light dark:border-white/[0.04] dark:bg-white/[0.02]">
                {{ detailBug.description }}
              </div>

              <!-- Screenshot -->
              <div v-if="detailBug.screenshot_url" class="mb-5">
                <a :href="detailBug.screenshot_url" target="_blank" class="block overflow-hidden rounded-xl border border-esmerald/[0.06] transition hover:border-esmerald/20 dark:border-white/[0.06] dark:hover:border-white/15">
                  <img :src="detailBug.screenshot_url" alt="Pantallazo" class="w-full object-contain" style="max-height: 300px" />
                </a>
              </div>

              <!-- Steps to reproduce -->
              <div v-if="detailBug.steps_to_reproduce && detailBug.steps_to_reproduce.length" class="mb-5">
                <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-green-light/60">Pasos para reproducir</p>
                <ol class="space-y-1.5">
                  <li v-for="(step, i) in detailBug.steps_to_reproduce" :key="i" class="flex items-start gap-2 text-sm text-green-light">
                    <span class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-esmerald/[0.06] text-[10px] font-bold dark:bg-white/[0.06]">{{ i + 1 }}</span>
                    <span>{{ step }}</span>
                  </li>
                </ol>
              </div>

              <!-- Expected vs Actual -->
              <div v-if="detailBug.expected_behavior || detailBug.actual_behavior" class="mb-5 grid grid-cols-2 gap-3">
                <div v-if="detailBug.expected_behavior" class="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3">
                  <p class="mb-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">Esperado</p>
                  <p class="text-xs leading-relaxed text-green-light">{{ detailBug.expected_behavior }}</p>
                </div>
                <div v-if="detailBug.actual_behavior" class="rounded-xl border border-red-500/20 bg-red-500/5 p-3">
                  <p class="mb-1 text-[10px] font-semibold uppercase tracking-wider text-red-600 dark:text-red-400">Actual</p>
                  <p class="text-xs leading-relaxed text-green-light">{{ detailBug.actual_behavior }}</p>
                </div>
              </div>

              <!-- Meta -->
              <div class="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Entorno</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ envLabel(detailBug.environment) }}</p>
                </div>
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Navegador</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ detailBug.device_browser || '—' }}</p>
                </div>
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Reportado por</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ detailBug.reported_by_name }}</p>
                </div>
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Fecha</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ formatDate(detailBug.created_at) }}</p>
                </div>
              </div>

              <!-- Admin response -->
              <div v-if="detailBug.admin_response" class="mb-5 rounded-xl border-l-2 border-l-esmerald/30 bg-esmerald-light/20 p-4 dark:border-l-lemon/40 dark:bg-white/[0.02]">
                <p class="mb-1 text-[10px] font-semibold uppercase tracking-wider text-esmerald/60 dark:text-lemon/60">Respuesta del equipo</p>
                <p class="text-sm leading-relaxed text-green-light">{{ detailBug.admin_response }}</p>
              </div>

              <!-- Admin actions -->
              <div v-if="authStore.isAdmin" class="mb-5 space-y-3">
                <div v-if="showEvaluateForm" class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]">
                  <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">Evaluar bug</p>
                  <div class="space-y-3">
                    <div>
                      <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Estado</label>
                      <select v-model="evalForm.status" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-2.5 text-sm text-esmerald outline-none focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                        <option value="reported">Reportado</option>
                        <option value="confirmed">Confirmado</option>
                        <option value="fixing">En corrección</option>
                        <option value="qa">En QA</option>
                        <option value="resolved">Resuelto</option>
                        <option value="not_reproducible">No reproducible</option>
                        <option value="wont_fix">No se corregirá</option>
                        <option value="duplicate">Duplicado</option>
                      </select>
                    </div>
                    <div>
                      <label class="mb-1 block text-xs font-medium text-esmerald/70 dark:text-white/70">Respuesta</label>
                      <textarea v-model="evalForm.admin_response" rows="2" placeholder="Respuesta para el cliente..." class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-2.5 text-sm text-esmerald outline-none placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                    </div>
                    <div class="flex justify-end gap-2">
                      <button type="button" class="rounded-lg px-3 py-1.5 text-xs text-green-light hover:text-esmerald dark:hover:text-white" @click="showEvaluateForm = false">Cancelar</button>
                      <button type="button" :disabled="bugStore.isUpdating" class="rounded-lg bg-esmerald px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-esmerald/90 disabled:opacity-50 dark:bg-lemon dark:text-esmerald-dark" @click="handleEvaluate">
                        {{ bugStore.isUpdating ? 'Guardando...' : 'Guardar' }}
                      </button>
                    </div>
                  </div>
                </div>

                <div v-else class="flex flex-wrap gap-2">
                  <button type="button" class="rounded-xl border border-esmerald/10 px-4 py-2 text-xs font-medium text-esmerald transition hover:bg-esmerald-light dark:border-white/10 dark:text-white dark:hover:bg-white/[0.06]" @click="openEvaluateForm">
                    Evaluar
                  </button>
                  <button type="button" class="rounded-xl border border-red-200 px-4 py-2 text-xs font-medium text-red-500 transition hover:bg-red-50 dark:border-red-500/20 dark:hover:bg-red-500/10" @click="handleDelete">
                    Eliminar
                  </button>
                </div>
              </div>

              <!-- Comments -->
              <div class="mb-4">
                <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">
                  Comentarios{{ detailBug.comments ? ` (${detailBug.comments.length})` : '' }}
                </p>

                <div v-if="detailBug.comments && detailBug.comments.length" class="mb-4 space-y-3">
                  <div
                    v-for="comment in detailBug.comments"
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

                <form class="flex gap-2" @submit.prevent="handleAddComment">
                  <input v-model="newComment" type="text" placeholder="Escribe un comentario..." class="flex-1 rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-2.5 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                  <button type="submit" :disabled="!newComment.trim()" class="rounded-xl bg-esmerald px-4 py-2.5 text-sm font-medium text-white transition hover:bg-esmerald/90 disabled:opacity-40 dark:bg-lemon dark:text-esmerald-dark">
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
import { usePlatformBugReportsStore } from '~/stores/platform-bug-reports'
import { usePlatformProjectsStore } from '~/stores/platform-projects'

definePageMeta({ layout: 'platform', middleware: ['platform-auth'] })
useHead({ title: 'Reporte de bugs — ProjectApp' })
usePageEntrance('#platform-bugs')

const route = useRoute()
const localePath = useLocalePath()
const authStore = usePlatformAuthStore()
const bugStore = usePlatformBugReportsStore()
const projectsStore = usePlatformProjectsStore()

const projectId = computed(() => route.params.id)
const projectName = computed(() => projectsStore.currentProject?.name || 'Proyecto')
const activeFilter = ref('all')

const statusTabs = computed(() => [
  { value: 'all', label: 'Todos', count: bugStore.bugReports.length },
  { value: 'reported', label: 'Reportados', count: bugStore.reportedCount },
  { value: 'confirmed', label: 'Confirmados', count: bugStore.confirmedCount },
  { value: 'fixing', label: 'En corrección', count: bugStore.fixingCount },
  { value: 'qa', label: 'En QA' },
  { value: 'resolved', label: 'Resueltos', count: bugStore.resolvedCount },
  { value: 'not_reproducible', label: 'No reproducible' },
  { value: 'wont_fix', label: 'No se corregirá' },
  { value: 'duplicate', label: 'Duplicado' },
])

const filteredBugs = computed(() => bugStore.filteredByStatus(activeFilter.value))

const isCreateOpen = ref(false)
const createForm = reactive({
  title: '', description: '', severity: 'medium', environment: 'production',
  device_browser: '', is_recurring: false, steps_to_reproduce: [''],
  expected_behavior: '', actual_behavior: '',
})
const screenshotFile = ref(null)
const screenshotPreview = ref(null)

const detailBug = ref(null)
const newComment = ref('')
const commentInternal = ref(false)
const showEvaluateForm = ref(false)
const evalForm = reactive({ status: 'confirmed', admin_response: '' })

function statusBadgeClass(s) {
  const map = {
    reported: 'bg-red-500/15 text-red-600 dark:text-red-400',
    confirmed: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    fixing: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    qa: 'bg-purple-500/15 text-purple-600 dark:text-purple-400',
    resolved: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    not_reproducible: 'bg-gray-500/15 text-gray-500',
    wont_fix: 'bg-gray-500/15 text-gray-500',
    duplicate: 'bg-gray-500/15 text-gray-500',
  }
  return map[s] || map.reported
}

function statusLabel(s) {
  const map = {
    reported: 'Reportado', confirmed: 'Confirmado', fixing: 'En corrección',
    qa: 'En QA', resolved: 'Resuelto', not_reproducible: 'No reproducible',
    wont_fix: 'No se corregirá', duplicate: 'Duplicado',
  }
  return map[s] || s
}

function severityBadgeClass(sev) {
  const map = {
    critical: 'bg-red-500/15 text-red-600 dark:text-red-400',
    high: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    medium: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    low: 'bg-gray-500/15 text-gray-500',
  }
  return map[sev] || map.medium
}

function severityLabel(sev) {
  const map = { critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja' }
  return map[sev] || sev
}

function envLabel(env) {
  const map = { production: 'Producción', staging: 'Staging', dev: 'Desarrollo' }
  return map[env] || env
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })
}

function openCreateModal() {
  createForm.title = ''; createForm.description = ''; createForm.severity = 'medium'
  createForm.environment = 'production'; createForm.device_browser = ''
  createForm.is_recurring = false; createForm.steps_to_reproduce = ['']
  createForm.expected_behavior = ''; createForm.actual_behavior = ''
  screenshotFile.value = null; screenshotPreview.value = null
  isCreateOpen.value = true
}

function handleScreenshotSelect(event) {
  const file = event.target.files?.[0]
  if (file) { screenshotFile.value = file; screenshotPreview.value = URL.createObjectURL(file) }
}
function handleScreenshotDrop(event) {
  const file = event.dataTransfer.files?.[0]
  if (file?.type.startsWith('image/')) { screenshotFile.value = file; screenshotPreview.value = URL.createObjectURL(file) }
}
function removeScreenshot() {
  screenshotFile.value = null
  if (screenshotPreview.value) URL.revokeObjectURL(screenshotPreview.value)
  screenshotPreview.value = null
}

async function handleCreate() {
  if (!createForm.title.trim()) return
  const steps = createForm.steps_to_reproduce.filter((s) => s.trim())
  let payload
  if (screenshotFile.value) {
    payload = new FormData()
    payload.append('title', createForm.title)
    payload.append('description', createForm.description)
    payload.append('severity', createForm.severity)
    payload.append('environment', createForm.environment)
    payload.append('device_browser', createForm.device_browser)
    payload.append('is_recurring', createForm.is_recurring)
    payload.append('expected_behavior', createForm.expected_behavior)
    payload.append('actual_behavior', createForm.actual_behavior)
    steps.forEach((s) => payload.append('steps_to_reproduce', s))
    payload.append('screenshot', screenshotFile.value)
  } else {
    payload = { ...createForm, steps_to_reproduce: steps }
  }
  const result = await bugStore.createBugReport(projectId.value, payload)
  if (result.success) {
    if (screenshotPreview.value) URL.revokeObjectURL(screenshotPreview.value)
    isCreateOpen.value = false
  }
}

async function openDetailModal(bug) {
  detailBug.value = bug; newComment.value = ''; commentInternal.value = false; showEvaluateForm.value = false
  const result = await bugStore.fetchBugReport(projectId.value, bug.id)
  if (result.success) detailBug.value = result.data
}

function openEvaluateForm() {
  evalForm.status = detailBug.value?.status || 'confirmed'
  evalForm.admin_response = detailBug.value?.admin_response || ''
  showEvaluateForm.value = true
}

async function handleEvaluate() {
  if (!detailBug.value) return
  const result = await bugStore.evaluateBugReport(projectId.value, detailBug.value.id, { ...evalForm })
  if (result.success) { detailBug.value = result.data; showEvaluateForm.value = false }
}

async function handleDelete() {
  if (!detailBug.value) return
  const result = await bugStore.deleteBugReport(projectId.value, detailBug.value.id)
  if (result.success) detailBug.value = null
}

async function handleAddComment() {
  if (!newComment.value.trim() || !detailBug.value) return
  const result = await bugStore.addComment(projectId.value, detailBug.value.id, newComment.value.trim(), commentInternal.value)
  if (result.success) { newComment.value = ''; commentInternal.value = false }
}

onMounted(async () => {
  await Promise.all([
    bugStore.fetchBugReports(projectId.value),
    projectsStore.currentProject?.id !== Number(projectId.value) ? projectsStore.fetchProject(projectId.value) : Promise.resolve(),
  ])
})
</script>

<style scoped>
.modal-overlay-enter-active, .modal-overlay-leave-active { transition: opacity 0.25s ease; }
.modal-overlay-enter-from, .modal-overlay-leave-to { opacity: 0; }
.modal-content-enter-active { transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-content-leave-active { transition: all 0.2s ease-in; }
.modal-content-enter-from { opacity: 0; transform: scale(0.95) translateY(10px); }
.modal-content-leave-to { opacity: 0; transform: scale(0.97); }
</style>
