<template>
  <div id="platform-deliverables">
    <!-- Loading -->
    <div v-if="store.isLoading && !store.deliverables.length" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <template v-else>
      <!-- Header -->
      <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between" data-enter>
        <div>
          <NuxtLink :to="localePath('/platform/deliverables')" class="mb-2 inline-flex items-center gap-1.5 text-sm text-green-light transition hover:text-esmerald dark:hover:text-white">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
            Entregables
          </NuxtLink>
          <h1 class="text-xl font-bold text-esmerald dark:text-white sm:text-2xl">Entregables</h1>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <label
            v-if="authStore.isAdmin"
            class="flex cursor-pointer items-center gap-2 rounded-full border border-esmerald/10 px-3 py-1.5 text-xs font-medium text-green-light dark:border-white/10"
          >
            <input v-model="includeArchived" type="checkbox" class="rounded border-esmerald/20 dark:border-white/20" />
            Mostrar archivados
          </label>
          <span class="rounded-full border border-esmerald/10 px-3 py-1.5 text-xs font-semibold text-green-light dark:border-white/10">
            {{ store.totalCount }} archivos
          </span>
          <button
            v-if="authStore.isAdmin"
            type="button"
            class="flex items-center gap-1.5 rounded-xl bg-lemon px-4 py-2 text-sm font-semibold text-esmerald-dark transition hover:brightness-105"
            @click="openCreateModal"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
            Subir archivo
          </button>
        </div>
      </div>

      <!-- Category filter -->
      <div class="mb-5 flex gap-1.5 overflow-x-auto pb-1" data-enter>
        <button
          v-for="tab in categoryTabs"
          :key="tab.value"
          type="button"
          class="shrink-0 rounded-full px-3.5 py-1.5 text-xs font-medium transition"
          :class="activeCategory === tab.value
            ? 'bg-esmerald text-white dark:bg-lemon dark:text-esmerald-dark'
            : 'text-green-light hover:bg-esmerald-light/50 dark:hover:bg-white/[0.06]'"
          @click="activeCategory = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Grouped by category -->
      <div v-if="filteredGroups.length" class="space-y-8" data-enter>
        <div v-for="group in filteredGroups" :key="group.category">
          <div class="mb-3 flex items-center gap-2">
            <span class="h-2 w-2 rounded-full" :class="categoryDotClass(group.category)" />
            <span class="text-xs font-semibold uppercase tracking-wider text-esmerald dark:text-white">{{ categoryLabel(group.category) }}</span>
            <span class="flex h-5 min-w-5 items-center justify-center rounded-full bg-esmerald/[0.06] px-1.5 text-[10px] font-bold text-green-light dark:bg-white/[0.06]">
              {{ group.items.length }}
            </span>
          </div>

          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div
              v-for="d in group.items"
              :key="d.id"
              class="group cursor-pointer rounded-2xl border border-esmerald/[0.06] bg-white p-5 transition hover:border-esmerald/15 hover:shadow-md dark:border-white/[0.06] dark:bg-esmerald dark:hover:border-white/12"
              :class="d.is_archived ? 'opacity-85' : ''"
              @click="openDetailModal(d)"
            >
              <div class="mb-3 flex items-start justify-between gap-2">
                <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" :class="categoryIconBg(d.category)">
                  <span class="text-lg">{{ categoryIcon(d.category) }}</span>
                </div>
                <div class="flex shrink-0 flex-col items-end gap-1">
                  <span v-if="d.is_archived" class="rounded-full bg-gray-500/15 px-2 py-0.5 text-[9px] font-semibold uppercase text-gray-600 dark:text-gray-400">
                    Archivado
                  </span>
                  <span class="rounded-full bg-esmerald/[0.06] px-2 py-0.5 text-[10px] font-semibold text-green-light dark:bg-white/[0.06]">
                    v{{ d.current_version }}
                  </span>
                </div>
              </div>
              <h4 class="text-sm font-semibold text-esmerald dark:text-white">{{ d.title }}</h4>
              <p v-if="d.description" class="mt-1 line-clamp-2 text-xs text-green-light">{{ d.description }}</p>
              <div class="mt-3 flex items-center justify-between text-[10px] text-green-light/60">
                <span>{{ d.file_name || '—' }}</span>
                <span>{{ formatDate(d.updated_at) }}</span>
              </div>
              <NuxtLink
                :to="localePath(`/platform/projects/${projectId}/deliverables/${d.id}`)"
                class="mt-3 inline-block text-xs font-medium text-esmerald dark:text-lemon"
                @click.stop
              >
                Ficha: documentos y Kanban →
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else class="py-16 text-center" data-enter>
        <div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-esmerald-light/50 dark:bg-white/[0.04]">
          <svg class="h-8 w-8 text-green-light/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
        </div>
        <p class="text-sm text-green-light">No hay entregables aún.</p>
        <button v-if="authStore.isAdmin" type="button" class="mt-4 rounded-xl bg-lemon px-5 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105" @click="openCreateModal">
          Subir primer archivo
        </button>
      </div>
    </template>

    <!-- Create modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div v-if="isCreateOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm" @click.self="isCreateOpen = false">
          <Transition name="modal-content" appear>
            <div v-if="isCreateOpen" class="w-full max-w-md rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <h2 class="mb-5 text-lg font-bold text-esmerald dark:text-white">Subir entregable</h2>
              <form class="space-y-4" @submit.prevent="handleCreate">
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Título <span class="text-red-400">*</span></label>
                  <input v-model="createForm.title" type="text" required placeholder="Nombre del entregable" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Descripción</label>
                  <textarea v-model="createForm.description" rows="2" placeholder="Descripción opcional..." class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Categoría</label>
                  <select v-model="createForm.category" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                    <option value="designs">Diseños</option>
                    <option value="credentials">Credenciales</option>
                    <option value="documents">Documentos</option>
                    <option value="contract">Contrato</option>
                    <option value="amendment">Otrosí</option>
                    <option value="legal_annex">Anexo legal</option>
                    <option value="apks">APKs / Builds</option>
                    <option value="other">Otros</option>
                  </select>
                </div>
                <!-- File upload -->
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Archivo <span class="text-red-400">*</span></label>
                  <div
                    class="relative flex min-h-[80px] cursor-pointer items-center justify-center rounded-xl border-2 border-dashed border-esmerald/15 bg-esmerald-light/20 transition hover:border-esmerald/30 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-white/20"
                    @click="$refs.fileInput.click()"
                    @dragover.prevent
                    @drop.prevent="handleFileDrop"
                  >
                    <input ref="fileInput" type="file" class="hidden" @change="handleFileSelect" />
                    <div v-if="!selectedFile" class="py-4 text-center">
                      <svg class="mx-auto mb-1.5 h-6 w-6 text-green-light/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                      <p class="text-[11px] text-green-light/50">Arrastra o haz clic para subir</p>
                    </div>
                    <div v-else class="flex w-full items-center gap-3 px-4 py-3">
                      <svg class="h-5 w-5 shrink-0 text-esmerald dark:text-lemon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                      <span class="flex-1 truncate text-sm text-esmerald dark:text-white">{{ selectedFile.name }}</span>
                      <button type="button" class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-green-light/40 hover:text-red-400" @click.stop="selectedFile = null">
                        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                      </button>
                    </div>
                  </div>
                </div>
                <div class="flex justify-end gap-3 pt-2">
                  <button type="button" class="rounded-xl border border-esmerald/10 px-5 py-2.5 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white" @click="isCreateOpen = false">Cancelar</button>
                  <button type="submit" :disabled="!createForm.title.trim() || !selectedFile || store.isUpdating" class="rounded-xl bg-lemon px-6 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50">
                    {{ store.isUpdating ? 'Subiendo...' : 'Subir' }}
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
        <div v-if="detailItem" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm" @click.self="detailItem = null">
          <Transition name="modal-content" appear>
            <div v-if="detailItem" class="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <div class="mb-5 flex items-start justify-between gap-4">
                <div class="flex-1">
                  <div class="mb-2 flex flex-wrap items-center gap-2">
                    <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase" :class="categoryBadgeClass(detailItem.category)">{{ categoryLabel(detailItem.category) }}</span>
                    <span class="rounded-full bg-esmerald/[0.06] px-2 py-0.5 text-[10px] font-semibold text-green-light dark:bg-white/[0.06]">v{{ detailItem.current_version }}</span>
                    <span v-if="detailItem.is_archived" class="rounded-full bg-gray-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-gray-600 dark:text-gray-400">
                      Archivado
                    </span>
                  </div>
                  <p v-if="detailItem.is_archived && detailItem.archived_at" class="mb-1 text-[10px] text-green-light/70">
                    Archivado el {{ formatDate(detailItem.archived_at) }}
                  </p>
                  <h2 class="text-lg font-bold text-esmerald dark:text-white">{{ detailItem.title }}</h2>
                </div>
                <button type="button" class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white" @click="detailItem = null">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              <div v-if="detailItem.description" class="mb-5 rounded-xl border border-esmerald/[0.04] bg-esmerald-light/20 p-4 text-sm leading-relaxed text-green-light dark:border-white/[0.04] dark:bg-white/[0.02]">
                {{ detailItem.description }}
              </div>

              <!-- Download current -->
              <a
                v-if="detailItem.file_url"
                :href="detailItem.file_url"
                target="_blank"
                class="mb-5 flex items-center gap-3 rounded-xl border border-esmerald/[0.06] bg-esmerald-light/20 p-4 transition hover:border-esmerald/20 dark:border-white/[0.06] dark:bg-white/[0.02] dark:hover:border-white/15"
              >
                <svg class="h-5 w-5 shrink-0 text-esmerald dark:text-lemon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                <div class="flex-1 min-w-0">
                  <p class="truncate text-sm font-medium text-esmerald dark:text-white">{{ detailItem.file_name }}</p>
                  <p class="text-[10px] text-green-light/60">Versión {{ detailItem.current_version }} · {{ detailItem.uploaded_by_name }} · {{ formatDate(detailItem.updated_at) }}</p>
                </div>
                <span class="text-xs font-medium text-esmerald dark:text-lemon">Descargar</span>
              </a>

              <!-- Meta -->
              <div class="mb-5 grid grid-cols-3 gap-3">
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Categoría</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ categoryLabel(detailItem.category) }}</p>
                </div>
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Subido por</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ detailItem.uploaded_by_name }}</p>
                </div>
                <div class="rounded-xl border border-esmerald/[0.04] p-3 dark:border-white/[0.04]">
                  <p class="text-[10px] font-medium uppercase tracking-wider text-green-light/60">Versiones</p>
                  <p class="mt-1 text-xs font-semibold text-esmerald dark:text-white">{{ detailItem.versions_count || detailItem.current_version }}</p>
                </div>
              </div>

              <!-- Version history -->
              <div v-if="detailItem.versions && detailItem.versions.length" class="mb-5">
                <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">Historial de versiones</p>
                <div class="space-y-2">
                  <a
                    v-for="v in detailItem.versions"
                    :key="v.id"
                    :href="v.file_url"
                    target="_blank"
                    class="flex items-center gap-3 rounded-xl border border-esmerald/[0.04] p-3 transition hover:border-esmerald/15 dark:border-white/[0.04] dark:hover:border-white/12"
                  >
                    <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-esmerald/[0.06] text-[10px] font-bold text-green-light dark:bg-white/[0.06]">v{{ v.version_number }}</span>
                    <div class="flex-1 min-w-0">
                      <p class="truncate text-xs font-medium text-esmerald dark:text-white">{{ v.file_name }}</p>
                      <p class="text-[10px] text-green-light/60">{{ v.uploaded_by_name }} · {{ formatDate(v.created_at) }}</p>
                    </div>
                    <svg class="h-4 w-4 shrink-0 text-green-light/30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 10v6m0 0l-3-3m3 3l3-3" /></svg>
                  </a>
                </div>
              </div>

              <!-- Admin actions -->
              <div v-if="authStore.isAdmin" class="flex flex-wrap gap-2">
                <button
                  v-if="detailItem.is_archived"
                  type="button"
                  class="rounded-xl border border-emerald-500/30 px-4 py-2 text-xs font-medium text-emerald-700 transition hover:bg-emerald-500/10 dark:border-emerald-500/25 dark:text-emerald-400 dark:hover:bg-emerald-500/10"
                  :disabled="store.isUpdating"
                  @click="handleRestore"
                >
                  {{ store.isUpdating ? '…' : 'Restaurar' }}
                </button>
                <button
                  v-else
                  type="button"
                  class="rounded-xl border border-esmerald/10 px-4 py-2 text-xs font-medium text-esmerald transition hover:bg-esmerald-light dark:border-white/10 dark:text-white dark:hover:bg-white/[0.06]"
                  @click="openUploadVersion"
                >
                  Subir nueva versión
                </button>
                <button
                  v-if="!detailItem.is_archived"
                  type="button"
                  class="rounded-xl border border-red-200 px-4 py-2 text-xs font-medium text-red-500 transition hover:bg-red-50 dark:border-red-500/20 dark:hover:bg-red-500/10"
                  :disabled="store.isUpdating"
                  @click="handleDelete"
                >
                  Archivar
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- Upload new version modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div v-if="isVersionUploadOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm" @click.self="isVersionUploadOpen = false">
          <Transition name="modal-content" appear>
            <div v-if="isVersionUploadOpen" class="w-full max-w-sm rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <h2 class="mb-4 text-lg font-bold text-esmerald dark:text-white">Nueva versión</h2>
              <p class="mb-4 text-xs text-green-light">Será la versión {{ (detailItem?.current_version || 0) + 1 }} de "{{ detailItem?.title }}"</p>
              <div
                class="relative mb-4 flex min-h-[80px] cursor-pointer items-center justify-center rounded-xl border-2 border-dashed border-esmerald/15 bg-esmerald-light/20 transition hover:border-esmerald/30 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-white/20"
                @click="$refs.versionFileInput.click()"
                @dragover.prevent
                @drop.prevent="handleVersionDrop"
              >
                <input ref="versionFileInput" type="file" class="hidden" @change="handleVersionSelect" />
                <div v-if="!versionFile" class="py-4 text-center">
                  <svg class="mx-auto mb-1.5 h-6 w-6 text-green-light/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                  <p class="text-[11px] text-green-light/50">Selecciona el archivo</p>
                </div>
                <div v-else class="flex w-full items-center gap-3 px-4 py-3">
                  <span class="flex-1 truncate text-sm text-esmerald dark:text-white">{{ versionFile.name }}</span>
                  <button type="button" class="text-green-light/40 hover:text-red-400" @click.stop="versionFile = null">
                    <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                </div>
              </div>
              <div class="flex justify-end gap-3">
                <button type="button" class="rounded-xl border border-esmerald/10 px-5 py-2.5 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white" @click="isVersionUploadOpen = false">Cancelar</button>
                <button type="button" :disabled="!versionFile || store.isUpdating" class="rounded-xl bg-lemon px-6 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50" @click="handleUploadVersion">
                  {{ store.isUpdating ? 'Subiendo...' : 'Subir versión' }}
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformIncludeArchived } from '~/composables/usePlatformIncludeArchived'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformDeliverablesStore } from '~/stores/platform-deliverables'
import { usePlatformProjectsStore } from '~/stores/platform-projects'

definePageMeta({ layout: 'platform', middleware: ['platform-auth'] })
usePageEntrance('#platform-deliverables')

const route = useRoute()
const localePath = useLocalePath()
const authStore = usePlatformAuthStore()
const store = usePlatformDeliverablesStore()
const projectsStore = usePlatformProjectsStore()
const includeArchived = usePlatformIncludeArchived()

const projectId = computed(() => route.params.id)
const projectName = computed(() => projectsStore.currentProject?.name || 'Proyecto')
const activeCategory = ref('all')

const categoryTabs = [
  { value: 'all', label: 'Todos' },
  { value: 'designs', label: 'Diseños' },
  { value: 'documents', label: 'Documentos' },
  { value: 'contract', label: 'Contrato' },
  { value: 'amendment', label: 'Otrosí' },
  { value: 'legal_annex', label: 'Anexo legal' },
  { value: 'credentials', label: 'Credenciales' },
  { value: 'apks', label: 'APKs / Builds' },
  { value: 'other', label: 'Otros' },
]

const filteredGroups = computed(() => {
  if (activeCategory.value === 'all') return store.groupedByCategory
  return store.groupedByCategory.filter((g) => g.category === activeCategory.value)
})

const isCreateOpen = ref(false)
const createForm = reactive({ title: '', description: '', category: 'other' })
const selectedFile = ref(null)

const detailItem = ref(null)
const isVersionUploadOpen = ref(false)
const versionFile = ref(null)

function categoryLabel(cat) {
  const map = {
    designs: 'Diseños', credentials: 'Credenciales', documents: 'Documentos',
    contract: 'Contrato', amendment: 'Otrosí', legal_annex: 'Anexo legal',
    apks: 'APKs / Builds', other: 'Otros',
  }
  return map[cat] || cat
}
function categoryDotClass(cat) {
  const map = {
    designs: 'bg-purple-500', credentials: 'bg-amber-500', documents: 'bg-blue-500',
    contract: 'bg-teal-500', amendment: 'bg-orange-500', legal_annex: 'bg-indigo-500',
    apks: 'bg-emerald-500', other: 'bg-gray-400',
  }
  return map[cat] || 'bg-gray-400'
}
function categoryIconBg(cat) {
  const map = {
    designs: 'bg-purple-500/10', credentials: 'bg-amber-500/10', documents: 'bg-blue-500/10',
    contract: 'bg-teal-500/10', amendment: 'bg-orange-500/10', legal_annex: 'bg-indigo-500/10',
    apks: 'bg-emerald-500/10', other: 'bg-gray-500/10',
  }
  return map[cat] || 'bg-gray-500/10'
}
function categoryIcon(cat) {
  const map = {
    designs: '🎨', credentials: '🔑', documents: '📄', contract: '📜', amendment: '✏️',
    legal_annex: '⚖️', apks: '📱', other: '📦',
  }
  return map[cat] || '📦'
}
function categoryBadgeClass(cat) {
  const map = {
    designs: 'bg-purple-500/15 text-purple-600 dark:text-purple-400',
    credentials: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    documents: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    contract: 'bg-teal-500/15 text-teal-600 dark:text-teal-400',
    amendment: 'bg-orange-500/15 text-orange-600 dark:text-orange-400',
    legal_annex: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400',
    apks: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400',
    other: 'bg-gray-500/15 text-gray-500',
  }
  return map[cat] || map.other
}
function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })
}

function openCreateModal() {
  createForm.title = ''; createForm.description = ''; createForm.category = 'other'
  selectedFile.value = null; isCreateOpen.value = true
}
function handleFileSelect(event) { selectedFile.value = event.target.files?.[0] || null }
function handleFileDrop(event) { selectedFile.value = event.dataTransfer.files?.[0] || null }

async function handleCreate() {
  if (!createForm.title.trim() || !selectedFile.value) return
  const fd = new FormData()
  fd.append('title', createForm.title)
  fd.append('description', createForm.description)
  fd.append('category', createForm.category)
  fd.append('file', selectedFile.value)
  const result = await store.createDeliverable(projectId.value, fd)
  if (result.success) isCreateOpen.value = false
}

async function openDetailModal(d) {
  detailItem.value = d
  const result = await store.fetchDeliverable(projectId.value, d.id)
  if (result.success) detailItem.value = result.data
}

function openUploadVersion() { versionFile.value = null; isVersionUploadOpen.value = true }
function handleVersionSelect(event) { versionFile.value = event.target.files?.[0] || null }
function handleVersionDrop(event) { versionFile.value = event.dataTransfer.files?.[0] || null }

async function handleUploadVersion() {
  if (!versionFile.value || !detailItem.value) return
  const fd = new FormData()
  fd.append('file', versionFile.value)
  const result = await store.uploadNewVersion(projectId.value, detailItem.value.id, fd)
  if (result.success) { detailItem.value = result.data; isVersionUploadOpen.value = false }
}

async function loadDeliverables() {
  await store.fetchDeliverables(projectId.value, null, authStore.isAdmin && includeArchived.value)
}

async function handleDelete() {
  if (!detailItem.value) return
  if (!window.confirm('¿Archivar este entregable? Podrás verlo otra vez activando "Mostrar archivados".')) return
  const result = await store.deleteDeliverable(projectId.value, detailItem.value.id)
  if (result.success) detailItem.value = null
}

async function handleRestore() {
  if (!detailItem.value?.is_archived) return
  const result = await store.updateDeliverable(projectId.value, detailItem.value.id, { is_archived: false })
  if (result.success) {
    detailItem.value = result.data
    await loadDeliverables()
  }
}

onMounted(async () => {
  await Promise.all([
    loadDeliverables(),
    projectsStore.currentProject?.id !== Number(projectId.value) ? projectsStore.fetchProject(projectId.value) : Promise.resolve(),
  ])
})

watch([includeArchived, projectId], () => {
  loadDeliverables()
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
