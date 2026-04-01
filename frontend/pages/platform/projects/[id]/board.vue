<template>
  <div id="platform-board">
    <!-- Loading -->
    <div v-if="reqStore.isLoading && !reqStore.requirements.length" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <template v-else>
      <!-- Header -->
      <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between" data-enter>
        <div>
          <NuxtLink :to="localePath('/platform/board')" class="mb-2 inline-flex items-center gap-1.5 text-sm text-green-light transition hover:text-esmerald dark:hover:text-white">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
            Tablero
          </NuxtLink>
          <h1 class="text-xl font-bold text-esmerald dark:text-white sm:text-2xl">Tablero</h1>
          <div v-if="deliverableFilterId" class="mt-2 flex flex-wrap items-center gap-2 text-xs">
            <span class="rounded-full border border-esmerald/15 bg-esmerald-light/30 px-3 py-1 font-medium text-esmerald dark:border-white/15 dark:bg-white/[0.06] dark:text-lemon">
              Solo este entregable
            </span>
            <NuxtLink
              :to="localePath(`/platform/projects/${projectId}/deliverables/${deliverableFilterId}`)"
              class="text-green-light underline decoration-green-light/30 transition hover:text-esmerald dark:hover:text-white"
            >
              Ficha del entregable
            </NuxtLink>
            <NuxtLink
              :to="localePath(`/platform/projects/${projectId}/board`)"
              class="text-green-light/80 underline decoration-transparent transition hover:text-esmerald dark:hover:text-white"
            >
              Ver todo el proyecto
            </NuxtLink>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <label
            v-if="authStore.isAdmin"
            class="flex cursor-pointer items-center gap-2 rounded-full border border-esmerald/10 px-3 py-2 text-xs font-medium text-green-light dark:border-white/10"
          >
            <input v-model="includeArchived" type="checkbox" class="rounded border-esmerald/20 dark:border-white/20" />
            Mostrar archivados
          </label>
          <!-- Progress pill -->
          <div class="flex items-center gap-2 rounded-full border border-esmerald/10 px-4 py-2 dark:border-white/10">
            <div class="h-2 w-16 overflow-hidden rounded-full bg-esmerald/[0.06] dark:bg-white/[0.06]">
              <div class="h-full rounded-full bg-esmerald transition-all duration-700 dark:bg-lemon" :style="{ width: `${reqStore.progressPercent}%` }" />
            </div>
            <span class="text-xs font-semibold text-esmerald dark:text-white">{{ reqStore.progressPercent }}%</span>
            <span class="text-xs text-green-light">{{ reqStore.doneCount }}/{{ reqStore.totalCount }}</span>
          </div>

          <!-- Add card button (admin) -->
          <template v-if="authStore.isAdmin">
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-xl border border-esmerald/10 px-3 py-2 text-xs font-medium text-green-light transition hover:border-esmerald/30 hover:text-esmerald dark:border-white/10 dark:hover:text-white"
              @click="downloadJsonExample"
            >
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              Ejemplo
            </button>
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-xl border border-esmerald/10 px-3 py-2 text-xs font-medium text-green-light transition hover:border-esmerald/30 hover:text-esmerald dark:border-white/10 dark:hover:text-white"
              @click="jsonUploadRef?.click()"
            >
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
              Subir JSON
            </button>
            <input ref="jsonUploadRef" type="file" accept=".json" class="hidden" @change="handleJsonUpload" />
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-xl bg-lemon px-4 py-2 text-sm font-semibold text-esmerald-dark transition hover:brightness-105"
              @click="openCreateModal()"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
              Card
            </button>
          </template>
        </div>
      </div>

      <!-- Backlog — flat list -->
      <div v-if="reqStore.backlogCount > 0" class="mb-6" data-enter>
        <button
          type="button"
          class="flex w-full items-center gap-3 rounded-2xl border border-esmerald/[0.04] bg-esmerald-light/20 px-5 py-4 text-left transition hover:bg-esmerald-light/40 dark:border-white/[0.04] dark:bg-white/[0.02] dark:hover:bg-white/[0.04]"
          @click="showBacklog = !showBacklog"
        >
          <svg class="h-4 w-4 shrink-0 text-gray-500 transition-transform duration-200" :class="showBacklog ? 'rotate-90' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
          <span class="text-sm font-semibold text-esmerald dark:text-white">Backlog</span>
          <span class="flex h-5 min-w-5 items-center justify-center rounded-full bg-esmerald/[0.06] px-1.5 text-[10px] font-bold text-green-light dark:bg-white/[0.06]">{{ reqStore.backlogCount }}</span>
        </button>

        <Transition name="done-list">
          <div v-if="showBacklog" class="mt-3 space-y-1 rounded-xl border border-esmerald/[0.04] bg-white px-3 py-2 dark:border-white/[0.04] dark:bg-esmerald">
            <div
              v-for="card in reqStore.backlogCards"
              :key="card.id"
              class="flex items-center gap-3 rounded-lg px-3 py-2.5 transition hover:bg-esmerald-light/30 dark:hover:bg-white/[0.03]"
            >
              <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-gray-400" />
              <button type="button" class="flex-1 text-left text-sm text-esmerald dark:text-white" @click="openDetailModal(card)">
                <span v-if="epicLabel(card)" class="mb-0.5 block text-[10px] font-semibold uppercase tracking-wide text-teal-600/80 dark:text-teal-300/80">{{ epicLabel(card) }}</span>
                {{ card.title }}
              </button>
              <button
                v-if="authStore.isAdmin"
                type="button"
                class="flex items-center gap-1 rounded-lg border border-esmerald/10 px-2 py-1 text-[10px] text-green-light transition hover:border-esmerald/30 hover:text-esmerald dark:border-white/10 dark:hover:text-white"
                @click="openMoveItemModal(card)"
              >
                <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
                Mover
              </button>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Kanban columns (full width grid) -->
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3" data-enter>
        <div
          v-for="col in reqStore.columns"
          :key="col.key"
          class="flex flex-col rounded-2xl border border-esmerald/[0.04] bg-esmerald-light/30 dark:border-white/[0.04] dark:bg-white/[0.02]"
        >
          <!-- Column header -->
          <div class="flex items-center justify-between px-4 py-3">
            <div class="flex items-center gap-2">
              <span class="h-2 w-2 rounded-full" :class="colDotClass(col.color)" />
              <span class="text-xs font-semibold uppercase tracking-wider text-esmerald dark:text-white">{{ col.label }}</span>
            </div>
            <span class="flex h-5 min-w-5 items-center justify-center rounded-full bg-esmerald/[0.06] px-1.5 text-[10px] font-bold text-green-light dark:bg-white/[0.06]">
              {{ col.cards.length }}
            </span>
          </div>

          <!-- Cards container (drop zone) -->
          <div
            class="kanban-column flex min-h-[80px] flex-1 flex-col gap-2 px-3 pb-3"
            :data-status="col.key"
            @dragover.prevent="handleDragOver($event, col.key)"
            @drop="handleDrop($event, col.key)"
            @dragleave="handleDragLeave($event)"
          >
            <div
              v-for="card in col.cards"
              :key="card.id"
              class="kanban-card group relative cursor-pointer rounded-xl border border-esmerald/[0.06] bg-white p-4 shadow-sm transition-all duration-200 hover:border-esmerald/15 hover:shadow-md dark:border-white/[0.06] dark:bg-esmerald dark:hover:border-white/12"
              :draggable="authStore.isAdmin"
              @dragstart="handleDragStart($event, card)"
              @dragend="handleDragEnd"
              @click="openDetailModal(card)"
            >
              <!-- Complete button (admin) -->
              <button
                v-if="authStore.isAdmin"
                type="button"
                class="absolute right-2.5 top-2.5 flex h-6 w-6 items-center justify-center rounded-full border border-esmerald/10 text-green-light/40 opacity-0 transition-all hover:border-emerald-500 hover:bg-emerald-500/10 hover:text-emerald-500 group-hover:opacity-100 dark:border-white/10 dark:hover:border-emerald-400 dark:hover:text-emerald-400"
                title="Marcar como completado"
                @click.stop="handleComplete(card)"
              >
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" /></svg>
              </button>

              <!-- Priority dot -->
              <div class="mb-2 flex items-center gap-2">
                <span class="h-1.5 w-1.5 rounded-full" :class="priorityDotClass(card.priority)" />
              </div>

              <p v-if="epicLabel(card)" class="mb-1 line-clamp-2 text-[10px] font-semibold uppercase tracking-wide text-teal-600/90 dark:text-teal-300/90">
                {{ epicLabel(card) }}
              </p>

              <!-- Title -->
              <h4 class="pr-6 text-sm font-medium leading-snug text-esmerald dark:text-white">{{ card.title }}</h4>

              <!-- Meta row -->
              <div class="mt-3 flex items-center justify-between">
                <span v-if="card.comments_count" class="flex items-center gap-1 text-[10px] text-green-light/60">
                  <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                  {{ card.comments_count }}
                </span>
                <span v-else />
                <span class="rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase" :class="priorityBadgeClass(card.priority)">
                  {{ priorityLabel(card.priority) }}
                </span>
              </div>
            </div>

            <!-- Drop indicator -->
            <div
              v-if="dragTarget === col.key"
              class="flex h-14 items-center justify-center rounded-xl border-2 border-dashed border-esmerald/20 text-xs text-green-light/40 dark:border-white/15"
            >
              Soltar aquí
            </div>
          </div>
        </div>
      </div>

      <!-- Completados (collapsible checklist) -->
      <div v-if="reqStore.doneCards.length" class="mt-6" data-enter>
        <button
          type="button"
          class="flex w-full items-center gap-3 rounded-2xl border border-esmerald/[0.04] bg-esmerald-light/20 px-5 py-4 text-left transition hover:bg-esmerald-light/40 dark:border-white/[0.04] dark:bg-white/[0.02] dark:hover:bg-white/[0.04]"
          @click="showDone = !showDone"
        >
          <svg
            class="h-4 w-4 shrink-0 text-emerald-500 transition-transform duration-200"
            :class="showDone ? 'rotate-90' : ''"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
          <span class="text-sm font-semibold text-esmerald dark:text-white">Completados</span>
          <span class="flex h-5 min-w-5 items-center justify-center rounded-full bg-emerald-500/15 px-1.5 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
            {{ reqStore.doneCards.length }}
          </span>
          <div class="ml-auto h-1.5 w-20 overflow-hidden rounded-full bg-esmerald/[0.06] dark:bg-white/[0.06]">
            <div class="h-full rounded-full bg-emerald-500 transition-all duration-700" :style="{ width: `${reqStore.progressPercent}%` }" />
          </div>
          <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400">{{ reqStore.progressPercent }}%</span>
        </button>

        <Transition name="done-list">
          <div v-if="showDone" class="mt-2 space-y-1.5 pl-1">
            <div
              v-for="card in reqStore.doneCards"
              :key="card.id"
              class="flex cursor-pointer items-center gap-3 rounded-xl px-4 py-3 transition hover:bg-esmerald-light/30 dark:hover:bg-white/[0.03]"
              @click="openDetailModal(card)"
            >
              <svg class="h-5 w-5 shrink-0 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="flex-1 text-sm text-green-light line-through decoration-green-light/30">
                <span v-if="epicLabel(card)" class="mb-0.5 block text-[10px] font-semibold uppercase tracking-wide text-teal-600/70 dark:text-teal-300/70">{{ epicLabel(card) }}</span>
                {{ card.title }}
              </span>
            </div>
          </div>
        </Transition>
      </div>
    </template>

    <!-- Move to column modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div v-if="isMoveOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm" @click.self="isMoveOpen = false">
          <Transition name="modal-content" appear>
            <div v-if="isMoveOpen" class="w-full max-w-sm rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <h2 class="mb-4 text-lg font-bold text-esmerald dark:text-white">Mover: {{ moveSingleCard?.title }}</h2>
              <form class="space-y-4" @submit.prevent="handleMoveSubmit">
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Columna destino</label>
                  <select v-model="moveForm.status" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                    <option value="todo">Por hacer</option>
                    <option value="in_progress">En progreso</option>
                    <option value="in_review">En revisión</option>
                  </select>
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Prioridad</label>
                  <select v-model="moveForm.priority" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                    <option value="low">Baja</option>
                    <option value="medium">Media</option>
                    <option value="high">Alta</option>
                    <option value="critical">Crítica</option>
                  </select>
                </div>
                <div class="flex justify-end gap-3 pt-2">
                  <button type="button" class="rounded-xl border border-esmerald/10 px-5 py-2.5 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white" @click="isMoveOpen = false">Cancelar</button>
                  <button type="submit" :disabled="isMoving" class="rounded-xl bg-lemon px-6 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50">
                    {{ isMoving ? 'Moviendo...' : 'Mover' }}
                  </button>
                </div>
              </form>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- Create requirement modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div
          v-if="isCreateOpen"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm"
          @click.self="isCreateOpen = false"
        >
          <Transition name="modal-content" appear>
            <div v-if="isCreateOpen" class="w-full max-w-md rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <h2 class="mb-5 text-lg font-bold text-esmerald dark:text-white">Nuevo requerimiento</h2>

              <form class="space-y-4" @submit.prevent="handleCreate">
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Título <span class="text-red-400">*</span></label>
                  <input v-model="createForm.title" type="text" required placeholder="Título del requerimiento" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Descripción</label>
                  <textarea v-model="createForm.description" rows="2" placeholder="Descripción del requerimiento..." class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Configuración</label>
                  <textarea v-model="createForm.configuration" rows="2" placeholder="Ej: Solo visible para rol Administrador..." class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                  <p class="mt-1 text-[10px] text-green-light/50">Roles, permisos o privilegios que aplican a este requerimiento.</p>
                </div>
                <div>
                  <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Flujo del usuario</label>
                  <textarea v-model="createForm.flow" rows="2" placeholder="Ej: El usuario ingresa → selecciona producto → agrega al carrito..." class="w-full resize-none rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition placeholder:text-green-light/50 focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:placeholder:text-white/30 dark:focus:border-lemon/40" />
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Prioridad</label>
                    <select v-model="createForm.priority" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                      <option value="low">Baja</option>
                      <option value="medium">Media</option>
                      <option value="high">Alta</option>
                      <option value="critical">Crítica</option>
                    </select>
                  </div>
                  <div>
                    <label class="mb-1.5 block text-xs font-medium text-esmerald/70 dark:text-white/70">Columna</label>
                    <select v-model="createForm.status" class="w-full rounded-xl border border-esmerald/10 bg-esmerald-light/40 px-4 py-3 text-sm text-esmerald outline-none transition focus:border-esmerald/30 dark:border-white/[0.08] dark:bg-esmerald-dark dark:text-white dark:focus:border-lemon/40">
                      <option value="backlog">Backlog</option>
                      <option value="todo">Por hacer</option>
                      <option value="in_progress">En progreso</option>
                      <option value="in_review">En revisión</option>
                    </select>
                  </div>
                </div>
                <div class="flex justify-end gap-3 pt-2">
                  <button type="button" class="rounded-xl border border-esmerald/10 px-5 py-2.5 text-sm text-green-light transition hover:text-esmerald dark:border-white/10 dark:hover:text-white" @click="isCreateOpen = false">Cancelar</button>
                  <button type="submit" :disabled="!createForm.title.trim() || reqStore.isUpdating" class="rounded-xl bg-lemon px-6 py-2.5 text-sm font-semibold text-esmerald-dark transition hover:brightness-105 disabled:opacity-50">
                    {{ reqStore.isUpdating ? 'Creando...' : 'Crear' }}
                  </button>
                </div>
              </form>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>

    <!-- Card detail modal -->
    <Teleport to="body">
      <Transition name="modal-overlay">
        <div
          v-if="detailCard"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm"
          @click.self="detailCard = null"
        >
          <Transition name="modal-content" appear>
            <div v-if="detailCard" class="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-esmerald/[0.06] bg-white p-6 shadow-2xl dark:border-white/[0.06] dark:bg-esmerald sm:p-8">
              <!-- Header -->
              <div class="mb-5 flex items-start justify-between gap-4">
                <div class="flex-1">
                  <div class="mb-2 flex flex-wrap items-center gap-2">
                    <span class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase" :class="priorityBadgeClass(detailCard.priority)">{{ priorityLabel(detailCard.priority) }}</span>
                    <span class="rounded-full bg-esmerald/[0.06] px-2.5 py-0.5 text-[10px] font-medium text-green-light dark:bg-white/[0.06]">{{ statusLabel(detailCard.status) }}</span>
                  </div>
                  <h2 class="text-lg font-bold text-esmerald dark:text-white">{{ detailCard.title }}</h2>
                  <p v-if="epicLabel(detailCard)" class="mt-2 text-xs font-medium text-teal-600 dark:text-teal-300">
                    Épica: {{ epicLabel(detailCard) }}
                  </p>
                  <p v-if="detailCard.source_flow_key" class="mt-1 text-[10px] text-green-light/70">
                    Ref. flujo: {{ detailCard.source_flow_key }}
                  </p>
                </div>
                <button type="button" class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-green-light transition hover:bg-esmerald-light hover:text-esmerald dark:hover:bg-white/[0.06] dark:hover:text-white" @click="detailCard = null">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>

              <!-- Description -->
              <div v-if="detailCard.description" class="mb-4">
                <p class="mb-1 text-[10px] font-medium uppercase tracking-wider text-green-light/60">Descripción</p>
                <div class="rounded-xl border border-esmerald/[0.04] bg-esmerald-light/20 p-4 text-sm leading-relaxed text-green-light dark:border-white/[0.04] dark:bg-white/[0.02]">{{ detailCard.description }}</div>
              </div>

              <!-- Configuration -->
              <div v-if="detailCard.configuration" class="mb-4">
                <p class="mb-1 text-[10px] font-medium uppercase tracking-wider text-green-light/60">Configuración (roles/permisos)</p>
                <div class="rounded-xl border border-amber-500/15 bg-amber-50/30 p-4 text-sm leading-relaxed text-green-light dark:border-amber-500/10 dark:bg-amber-900/10">{{ detailCard.configuration }}</div>
              </div>

              <!-- Flow -->
              <div v-if="detailCard.flow" class="mb-5">
                <p class="mb-1 text-[10px] font-medium uppercase tracking-wider text-green-light/60">Flujo del usuario</p>
                <div class="rounded-xl border border-blue-500/15 bg-blue-50/30 p-4 text-sm leading-relaxed text-green-light dark:border-blue-500/10 dark:bg-blue-900/10">{{ detailCard.flow }}</div>
              </div>

              <!-- Client review actions for completed items -->
              <div v-if="!authStore.isAdmin && detailCard.status === 'done'" class="mb-5">
                <p class="mb-2 text-xs font-semibold text-esmerald dark:text-white">¿Este requerimiento cumple con lo esperado?</p>
                <div class="flex gap-2">
                  <button type="button" class="flex-1 rounded-xl bg-emerald-500 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-600" @click="handleApprove">Aprobar</button>
                  <NuxtLink :to="localePath(`/platform/projects/${projectId}/changes?from_req=${detailCard.id}&title=${encodeURIComponent(detailCard.title)}`)" class="flex flex-1 items-center justify-center rounded-xl border border-amber-500/30 py-2.5 text-sm font-semibold text-amber-600 transition hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/10">Solicitar cambio</NuxtLink>
                  <NuxtLink :to="localePath(`/platform/projects/${projectId}/bugs?from_req=${detailCard.id}&title=${encodeURIComponent(detailCard.title)}`)" class="flex flex-1 items-center justify-center rounded-xl border border-red-500/30 py-2.5 text-sm font-semibold text-red-600 transition hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/10">Reportar bug</NuxtLink>
                </div>
              </div>

              <!-- History -->
              <div v-if="detailCard.history && detailCard.history.length" class="mb-5">
                <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">Historial</p>
                <div class="space-y-2">
                  <div v-for="entry in detailCard.history" :key="entry.id" class="flex items-center gap-2 text-xs text-green-light">
                    <span class="rounded-full bg-esmerald/[0.06] px-2 py-0.5 font-medium dark:bg-white/[0.06]">{{ statusLabel(entry.from_status) }}</span>
                    <svg class="h-3 w-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
                    <span class="rounded-full bg-esmerald/[0.06] px-2 py-0.5 font-medium dark:bg-white/[0.06]">{{ statusLabel(entry.to_status) }}</span>
                    <span class="ml-auto text-green-light/40">{{ formatDate(entry.created_at) }}</span>
                  </div>
                </div>
              </div>

              <!-- Comments -->
              <div class="mb-4">
                <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">
                  Comentarios{{ detailCard.comments ? ` (${detailCard.comments.length})` : '' }}
                </p>

                <div v-if="detailCard.comments && detailCard.comments.length" class="mb-4 space-y-3">
                  <div
                    v-for="comment in detailCard.comments"
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformProjectsStore } from '~/stores/platform-projects'
import { usePlatformRequirementsStore } from '~/stores/platform-requirements'
import { usePlatformApi } from '~/composables/usePlatformApi'
import { buildPlatformListUrl } from '~/composables/useIncludeArchivedQuery'
import { usePlatformIncludeArchived } from '~/composables/usePlatformIncludeArchived'

definePageMeta({
  layout: 'platform',
  middleware: ['platform-auth'],
})

useHead({ title: 'Tablero — ProjectApp' })
usePageEntrance('#platform-board')

const route = useRoute()
const deliverableFilterId = computed(() => route.query.deliverable_id || null)
const localePath = useLocalePath()
const authStore = usePlatformAuthStore()
const projectsStore = usePlatformProjectsStore()
const reqStore = usePlatformRequirementsStore()
const includeArchived = usePlatformIncludeArchived()

const projectId = computed(() => route.params.id)
/** Resolved entregable for nested requirements API (query filter or default). */
const activeDeliverableId = ref(null)
const projectName = computed(() => projectsStore.currentProject?.name || 'Proyecto')

const isCreateOpen = ref(false)
const createForm = reactive({ title: '', description: '', configuration: '', flow: '', priority: 'medium', status: 'backlog' })

const detailCard = ref(null)
const newComment = ref('')
const commentInternal = ref(false)
const showDone = ref(false)
const showBacklog = ref(false)

const isMoveOpen = ref(false)
const moveSingleCard = ref(null)
const isMoving = ref(false)
const moveForm = reactive({ status: 'todo', priority: 'medium' })

const jsonUploadRef = ref(null)
const jsonUploadError = ref('')

const draggedCard = ref(null)
const dragTarget = ref(null)

function colDotClass(color) {
  const map = { gray: 'bg-gray-400', blue: 'bg-blue-500', amber: 'bg-amber-500', purple: 'bg-purple-500', teal: 'bg-teal-500', green: 'bg-emerald-500' }
  return map[color] || 'bg-gray-400'
}

function priorityDotClass(priority) {
  const map = { critical: 'bg-red-500', high: 'bg-amber-500', medium: 'bg-blue-400', low: 'bg-gray-400' }
  return map[priority] || 'bg-gray-400'
}

function priorityBadgeClass(priority) {
  const map = {
    critical: 'bg-red-500/15 text-red-600 dark:text-red-400',
    high: 'bg-amber-500/15 text-amber-600 dark:text-amber-400',
    medium: 'bg-blue-500/15 text-blue-600 dark:text-blue-400',
    low: 'bg-gray-500/15 text-gray-500',
  }
  return map[priority] || map.medium
}

function priorityLabel(p) {
  const map = { critical: 'Crítica', high: 'Alta', medium: 'Media', low: 'Baja' }
  return map[p] || p
}

function epicLabel(card) {
  if (!card) return ''
  return (card.source_epic_title || card.source_epic_key || '').trim()
}

function statusLabel(s) {
  const map = { backlog: 'Backlog', todo: 'Por hacer', in_progress: 'En progreso', in_review: 'En revisión', approval: 'Aprobación', done: 'Completado' }
  return map[s] || s
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })
}

function downloadJsonExample() {
  const example = [
    {
      title: 'Login de usuario',
      description: 'Pantalla de autenticación con email y contraseña.',
      configuration: 'Todos los usuarios.',
      flow: 'Usuario abre la app → ingresa email y contraseña → click en Iniciar sesión → redirige al dashboard.',
    },
    {
      title: 'Panel de administración',
      description: 'Vista principal del administrador con métricas y accesos rápidos.',
      configuration: 'Solo rol: Administrador.',
      flow: 'Admin inicia sesión → ve dashboard con KPIs → puede navegar a gestión de usuarios, productos, pedidos.',
    },
    {
      title: 'Catálogo de productos',
      description: 'Listado de productos con filtros y búsqueda.',
      configuration: 'Visible para todos los usuarios registrados.',
      flow: 'Usuario navega al catálogo → puede filtrar por categoría → click en producto → ve detalle.',
      priority: 'high',
    },
  ]
  const blob = new Blob([JSON.stringify(example, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'requerimientos-ejemplo.json'
  a.click()
  URL.revokeObjectURL(url)
}

function openMoveItemModal(card) {
  moveSingleCard.value = card
  moveForm.status = 'todo'
  moveForm.priority = card.priority || 'medium'
  isMoveOpen.value = true
}

async function handleMoveSubmit() {
  if (!moveSingleCard.value || !activeDeliverableId.value) return
  isMoving.value = true
  try {
    await reqStore.updateRequirement(
      projectId.value,
      activeDeliverableId.value,
      moveSingleCard.value.id,
      { priority: moveForm.priority },
    )
    await reqStore.moveRequirement(
      projectId.value,
      activeDeliverableId.value,
      moveSingleCard.value.id,
      moveForm.status,
      0,
    )
    isMoveOpen.value = false
  } finally {
    isMoving.value = false
  }
}

async function handleJsonUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  jsonUploadError.value = ''

  try {
    const text = await file.text()
    const items = JSON.parse(text)
    if (!Array.isArray(items)) {
      jsonUploadError.value = 'El JSON debe ser un array de objetos.'
      return
    }
    if (!activeDeliverableId.value) {
      jsonUploadError.value = 'No hay entregable seleccionado.'
      return
    }
    const result = await reqStore.bulkUpload(projectId.value, activeDeliverableId.value, items)
    if (result.success) {
      jsonUploadError.value = ''
      alert(`Se crearon ${result.data.created} requerimientos.`)
    } else {
      jsonUploadError.value = result.message
    }
  } catch {
    jsonUploadError.value = 'Error leyendo el archivo JSON.'
  } finally {
    if (jsonUploadRef.value) jsonUploadRef.value.value = ''
  }
}

function handleDragStart(event, card) {
  draggedCard.value = card
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', card.id)
  event.target.style.opacity = '0.5'
}

function handleDragEnd(event) {
  event.target.style.opacity = '1'
  draggedCard.value = null
  dragTarget.value = null
}

function handleDragOver(event, colKey) {
  event.dataTransfer.dropEffect = 'move'
  dragTarget.value = colKey
}

function handleDragLeave(event) {
  if (!event.currentTarget.contains(event.relatedTarget)) {
    dragTarget.value = null
  }
}

async function handleDrop(event, colKey) {
  dragTarget.value = null
  if (!draggedCard.value) return

  const card = draggedCard.value
  draggedCard.value = null

  if (card.status === colKey) return

  if (!activeDeliverableId.value) return
  await reqStore.moveRequirement(projectId.value, activeDeliverableId.value, card.id, colKey, 0)
}

function openCreateModal() {
  createForm.title = ''
  createForm.description = ''
  createForm.configuration = ''
  createForm.flow = ''
  createForm.priority = 'medium'
  createForm.status = 'backlog'
  isCreateOpen.value = true
}

async function handleComplete(card) {
  if (!activeDeliverableId.value) return
  await reqStore.moveRequirement(projectId.value, activeDeliverableId.value, card.id, 'done', 0)
}

async function handleCreate() {
  if (!createForm.title.trim()) return
  if (!activeDeliverableId.value) return
  const result = await reqStore.createRequirement(projectId.value, activeDeliverableId.value, { ...createForm })
  if (result.success) isCreateOpen.value = false
}

async function openDetailModal(card) {
  detailCard.value = card
  newComment.value = ''
  commentInternal.value = false
  if (!activeDeliverableId.value) return
  const result = await reqStore.fetchRequirement(projectId.value, activeDeliverableId.value, card.id)
  if (result.success) detailCard.value = result.data
}

async function handleAddComment() {
  if (!newComment.value.trim() || !detailCard.value) return
  if (!activeDeliverableId.value) return
  const result = await reqStore.addComment(
    projectId.value,
    activeDeliverableId.value,
    detailCard.value.id,
    newComment.value.trim(),
    commentInternal.value,
  )
  if (result.success) {
    newComment.value = ''
    commentInternal.value = false
  }
}

async function handleApprove() {
  if (!detailCard.value) return
  if (!activeDeliverableId.value) return
  const result = await reqStore.moveRequirement(
    projectId.value,
    activeDeliverableId.value,
    detailCard.value.id,
    'done',
    0,
  )
  if (result.success) {
    detailCard.value = null
  }
}

async function resolveBoardDeliverableId() {
  if (deliverableFilterId.value) return Number(deliverableFilterId.value)
  const { get } = usePlatformApi()
  const url = buildPlatformListUrl(
    `projects/${projectId.value}/deliverables/`,
    {},
    authStore.isAdmin && includeArchived.value,
  )
  const dres = await get(url)
  const list = dres.data || []
  const withBp = list.find((d) => d.has_business_proposal)
  return (withBp || list[0])?.id ?? null
}

async function refreshBoardDeliverable() {
  const did = await resolveBoardDeliverableId()
  activeDeliverableId.value = did
  if (!did) {
    reqStore.requirements = []
    return
  }
  await reqStore.fetchRequirements(projectId.value, did)
}

onMounted(async () => {
  if (projectsStore.currentProject?.id !== Number(projectId.value)) {
    await projectsStore.fetchProject(projectId.value)
  }
  await refreshBoardDeliverable()
})

watch(deliverableFilterId, () => {
  refreshBoardDeliverable()
})

watch(includeArchived, () => {
  if (authStore.isAdmin) refreshBoardDeliverable()
})
</script>

<style scoped>
.kanban-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(0,0,0,0.1) transparent;
}
.kanban-scroll::-webkit-scrollbar {
  height: 6px;
}
.kanban-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.kanban-scroll::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.1);
  border-radius: 3px;
}

.kanban-card {
  user-select: none;
}
.kanban-card[draggable="true"]:active {
  cursor: grabbing;
}

.done-list-enter-active { transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.done-list-leave-active { transition: all 0.2s ease-in; }
.done-list-enter-from { opacity: 0; max-height: 0; overflow: hidden; }
.done-list-enter-to { opacity: 1; max-height: 1000px; }
.done-list-leave-from { opacity: 1; max-height: 1000px; }
.done-list-leave-to { opacity: 0; max-height: 0; overflow: hidden; }

.modal-overlay-enter-active,
.modal-overlay-leave-active { transition: opacity 0.25s ease; }
.modal-overlay-enter-from,
.modal-overlay-leave-to { opacity: 0; }
.modal-content-enter-active { transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-content-leave-active { transition: all 0.2s ease-in; }
.modal-content-enter-from { opacity: 0; transform: scale(0.95) translateY(10px); }
.modal-content-leave-to { opacity: 0; transform: scale(0.97); }
</style>
