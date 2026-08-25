<template>
  <div class="w-full">
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
      <div class="min-w-0">
        <NuxtLink
          :to="localePath('/panel/documents')"
          class="inline-flex items-center gap-1 text-sm text-text-muted hover:text-text-default transition-colors"
          aria-label="Volver a documentos"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Volver a documentos
        </NuxtLink>
        <h1 class="text-2xl font-light text-text-default mt-2 truncate">
          {{ documentStore.currentDocument?.title || 'Editar Documento' }}
        </h1>
        <p v-if="documentStore.currentDocument" class="text-sm text-text-muted mt-1">
          {{ statusLabel }}{{ headerClientLabel ? ` · ${headerClientLabel}` : '' }}
        </p>
      </div>
      <div v-if="documentStore.currentDocument && !loadError" class="hidden items-center gap-3 panel-landscape:flex">
        <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-text-muted hover:text-text-default">
          Cancelar
        </NuxtLink>
        <BaseDropdown :items="downloadItems" align="right">
          <template #trigger>
            <BaseButton variant="secondary" size="md" :disabled="isDownloading">
              {{ isDownloading ? 'Descargando...' : 'Descargar PDF' }}
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </BaseButton>
          </template>
        </BaseDropdown>
        <BaseButton
          variant="primary"
          size="md"
          type="submit"
          form="doc-edit-form"
          data-testid="doc-save-desktop"
          :disabled="documentStore.isUpdating || !hasChanges || lockedCuenta"
        >
          {{ documentStore.isUpdating ? 'Guardando...' : (hasChanges ? 'Guardar cambios' : 'Guardar') }}
        </BaseButton>
      </div>
    </div>

    <!-- Llegar por URL directa a un archivado no daría ninguna señal de que
         está fuera de circulación: la lista ya no lo muestra. -->
    <BaseAlert
      v-if="documentStore.currentDocument?.is_archived && !loadError"
      variant="warning"
      title="Este documento está archivado"
      class="mb-6"
      data-testid="document-archived-banner"
    >
      <p>No aparece en el listado, en la búsqueda ni en los contadores.</p>
      <div class="mt-3">
        <BaseButton
          variant="secondary"
          size="sm"
          :loading="documentStore.isUpdating"
          @click="handleUnarchive"
        >
          Restaurar
        </BaseButton>
      </div>
    </BaseAlert>

    <div
      v-if="documentStore.isLoading"
      class="grid grid-cols-1 gap-6 panel-landscape:grid-cols-[20rem_minmax(0,1fr)] panel-desktop:grid-cols-[24rem_minmax(0,1fr)]"
      role="status"
    >
      <span class="sr-only">Cargando documento...</span>
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-6 space-y-4" aria-hidden="true">
        <BaseSkeleton class="w-1/3" />
        <BaseSkeleton variant="card" class="!h-10" />
        <BaseSkeleton variant="card" class="!h-10" />
        <BaseSkeleton variant="card" class="!h-10" />
      </div>
      <div class="bg-surface rounded-xl shadow-sm border border-border-muted p-6" aria-hidden="true">
        <BaseSkeleton variant="card" class="!h-96" />
      </div>
    </div>

    <BaseAlert v-else-if="loadError" variant="danger" title="No se pudo cargar el documento">
      <p>Verifica tu conexión e inténtalo de nuevo.</p>
      <div class="mt-3 flex items-center gap-4">
        <BaseButton variant="secondary" size="sm" @click="reloadDocument">Reintentar</BaseButton>
        <NuxtLink
          :to="localePath('/panel/documents')"
          class="text-sm text-text-brand hover:underline"
        >
          ← Volver a la lista
        </NuxtLink>
      </div>
    </BaseAlert>

    <form
      v-else-if="documentStore.currentDocument"
      id="doc-edit-form"
      class="grid grid-cols-1 gap-6 panel-landscape:grid-cols-[20rem_minmax(0,1fr)] panel-desktop:grid-cols-[24rem_minmax(0,1fr)]"
      @submit.prevent="handleSave"
    >
      <!-- Requisito 6: un documento emitido no se reasigna ni se reescribe.
           El form queda visible (consultarlo sigue valiendo) con el guardado
           apagado; el backend rechaza igual con collection_account_locked. -->
      <BaseAlert
        v-if="lockedCuenta"
        variant="warning"
        class="panel-landscape:col-span-2"
        data-testid="doc-locked-cuenta-alert"
      >
        Cuenta de cobro emitida: este documento es de sólo lectura aquí.
        Si hubo un error, anúlala y emite una nueva desde
        Contabilidad → Cuentas de cobro.
      </BaseAlert>

      <!-- El botón Guardar habilitado se lee como "puedes guardar"; esto se
           lee como "te falta guardar", y nombra qué falta. -->
      <UnsavedChangesNotice
        v-if="hasChanges"
        class="panel-landscape:col-span-2"
        :title="unsavedTitle"
        :detail="unsavedDetail"
        :message="lockedCuenta
          ? 'Esta cuenta de cobro está emitida: estos cambios no se pueden guardar y se pierden al salir.'
          : 'Si sales de esta página, se pierden. Guardar los deja registrados.'"
        :can-save="canSaveNow"
        :saving="documentStore.isUpdating"
        testid="doc-unsaved-notice"
        @save="handleSave"
        @discard="discardChanges"
      />

      <aside
        class="bg-surface rounded-xl shadow-sm border border-border-muted p-5 sm:p-6
               panel-landscape:sticky panel-landscape:top-6 panel-landscape:self-start panel-landscape:max-h-[calc(100vh-7rem)] panel-landscape:overflow-y-auto"
      >
        <div class="space-y-6">
          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-text-muted">Identificación</h2>
            <div>
              <!-- La marca va FUERA del <label>: dentro se sumaba al nombre
                   accesible del campo ("Título Sin guardar"). -->
              <div class="flex items-center gap-2 mb-1">
                <label for="edit-title" class="block text-sm font-medium text-text-default">Título</label>
                <BaseBadge
                  v-if="isFieldDirty('title')"
                  variant="warning"
                  size="sm"
                  data-testid="doc-field-dirty-title"
                >
                  Sin guardar
                </BaseBadge>
              </div>
              <input
                id="edit-title"
                v-model="form.title"
                type="text"
                required
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              />
            </div>
            <div class="rounded-xl border border-border-default bg-surface-raised p-3">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <p class="text-sm font-medium text-text-default">Notas</p>
                    <BaseBadge v-if="notesDirty" variant="warning" size="sm">Sin guardar</BaseBadge>
                    <BaseBadge v-else-if="hasNotes" variant="success" size="sm">Agregadas</BaseBadge>
                  </div>
                  <p class="text-xs text-text-subtle mt-1">Asunto, correo, WhatsApp y notas personalizadas.</p>
                </div>
                <BaseButton
                  type="button"
                  variant="secondary"
                  size="sm"
                  :icon-only="!lockedCuenta"
                  :aria-label="lockedCuenta ? undefined : notesActionLabel"
                  :title="lockedCuenta ? undefined : notesActionLabel"
                  :disabled="lockedCuenta && !hasNotes"
                  data-testid="doc-client-note-open"
                  @click="showClientNote = true"
                >
                  <span v-if="lockedCuenta">Ver notas</span>
                  <span v-else aria-hidden="true">{{ hasNotes ? '✏️' : '📝' }}</span>
                </BaseButton>
              </div>
            </div>
            <div>
              <div class="flex items-center gap-2 mb-1">
                <label class="block text-sm font-medium text-text-default">Cliente</label>
                <BaseBadge
                  v-if="isFieldDirty('client')"
                  variant="warning"
                  size="sm"
                  data-testid="doc-field-dirty-client"
                >
                  Sin guardar
                </BaseBadge>
              </div>
              <ClientAutocomplete
                v-model="form.client"
                :initial-label="clientDisplayName"
                test-id="doc-client-autocomplete"
                @select="onClientSelect"
                @create-new="onCreateNewClient"
              />
              <p
                v-if="!form.client && legacyClientName"
                class="text-xs text-text-subtle mt-1"
                data-testid="doc-legacy-client-name"
              >
                Nombre guardado (texto libre): {{ legacyClientName }}
              </p>
              <!-- La relación sirve en las dos direcciones: desde el documento
                   se llega a su cliente y a su proyecto. -->
              <div
                v-if="savedClientId || savedProjectId"
                class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs"
              >
                <NuxtLink
                  v-if="savedClientId"
                  data-testid="document-client-link"
                  :to="localePath({ path: '/panel/clients', query: { highlight: String(savedClientId) } })"
                  class="text-text-brand hover:underline"
                >
                  Ver cliente{{ savedClientLabel ? `: ${savedClientLabel}` : '' }}
                </NuxtLink>
                <NuxtLink
                  v-if="savedProjectId"
                  data-testid="document-project-link"
                  :to="localePath({ path: '/panel/projects', query: { highlight: String(savedProjectId) } })"
                  class="text-text-brand hover:underline"
                >
                  Ver proyecto{{ savedProjectName ? `: ${savedProjectName}` : '' }}
                </NuxtLink>
              </div>
            </div>

            <!-- Inline client creation: the clients module without leaving the form -->
            <div
              v-if="inlineClientOpen"
              class="rounded-xl border border-border-default bg-surface-raised p-4 space-y-3"
              data-testid="doc-inline-client"
            >
              <p class="text-sm font-medium text-text-default">Crear cliente nuevo</p>
              <ClientFormFields
                v-model="inlineClient"
                testid-prefix="doc-inline-client"
                dense
              />
              <div class="flex justify-end gap-2">
                <BaseButton type="button" variant="secondary" size="sm" @click="inlineClientOpen = false">
                  Cancelar
                </BaseButton>
                <BaseButton
                  type="button"
                  variant="primary"
                  size="sm"
                  :disabled="creatingClient"
                  data-testid="doc-inline-client-save"
                  @click="createInlineClient"
                >
                  {{ creatingClient ? 'Creando...' : 'Crear cliente' }}
                </BaseButton>
              </div>
            </div>

            <div>
              <ProjectSelect
                v-model="form.project"
                :client-profile-id="form.client"
                :client-label="clientDisplayName"
                :allow-no-client="true"
                testid="doc-project-select"
                @select="onProjectSelect"
              />
              <!-- ProjectSelect dibuja su propia etiqueta, así que la marca va
                   debajo del campo en vez de al lado del rótulo. -->
              <BaseBadge
                v-if="isFieldDirty('project')"
                variant="warning"
                size="sm"
                class="mt-1"
                data-testid="doc-field-dirty-project"
              >
                Sin guardar
              </BaseBadge>
            </div>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Estado</label>
              <select
                v-model="form.status"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              >
                <option v-for="option in statusOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>

          <hr class="border-border-muted" />

          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-text-muted">Organización</h2>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Carpeta</label>
              <select
                v-model="form.folder_id"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              >
                <option :value="null">Sin carpeta</option>
                <option v-for="folder in folderStore.activeFolders" :key="folder.id" :value="folder.id">
                  {{ folder.name }}
                </option>
              </select>
            </div>
            <TagSelector v-model="form.tag_ids" :tags="tagStore.tags" />
          </div>

          <hr class="border-border-muted" />

          <div class="space-y-4">
            <h2 class="text-xs uppercase tracking-wide font-semibold text-text-muted">Opciones de exportación</h2>
            <div>
              <label class="block text-sm font-medium text-text-default mb-1">Idioma</label>
              <select
                v-model="form.language"
                class="w-full px-4 py-2.5 border border-border-default rounded-xl text-sm bg-surface text-text-default
                       focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none"
              >
                <option value="es">Español</option>
                <option value="en">English</option>
              </select>
            </div>
            <div class="space-y-1">
              <label
                v-for="option in coverOptions"
                :key="option.key"
                class="flex items-center gap-3 cursor-pointer py-1.5 px-1 select-none"
                :data-testid="option.testId"
              >
                <BaseToggle v-model="form[option.key]" />
                <span class="text-sm font-medium text-text-default">{{ option.label }}</span>
              </label>
              <!-- Traduce las casillas a páginas: sin esto, saber qué trae el
                   archivo obligaba a descargarlo. -->
              <p class="text-xs text-text-subtle pt-1 px-1" data-testid="doc-included-pages">
                El PDF incluirá: {{ includedPagesLabel }}
              </p>
              <BaseButton
                variant="secondary"
                size="sm"
                class="mt-2 w-full"
                data-testid="doc-preview-pdf"
                @click="handlePreviewPdf"
              >
                Previsualizar PDF
              </BaseButton>
            </div>
          </div>
        </div>
      </aside>

      <section
        class="bg-surface rounded-xl shadow-sm border border-border-muted p-5 sm:p-6
               flex flex-col min-w-0"
      >
        <div class="flex items-center justify-between mb-3 gap-3 flex-wrap">
          <label for="edit-markdown" class="block text-sm font-medium text-text-default">Contenido Markdown</label>
          <div class="flex items-center gap-2 flex-wrap">
            <span v-if="form.content_markdown" class="text-xs text-text-subtle tabular-nums">
              {{ form.content_markdown.length.toLocaleString() }} caracteres
            </span>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors"
              :class="copiedMarkdown
                ? 'bg-primary-soft text-text-brand hover:bg-primary-soft'
                : 'bg-surface-raised text-text-muted hover:bg-surface-raised'"
              :disabled="!form.content_markdown.trim()"
              @click="handleCopyContent"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              {{ copiedMarkdown ? 'Copiado' : 'Copiar' }}
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors"
              :class="pastedMarkdown
                ? 'bg-primary-soft text-text-brand hover:bg-primary-soft'
                : 'bg-surface-raised text-text-muted hover:bg-surface-raised'"
              @click="handlePasteContent"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              {{ pastedMarkdown ? 'Pegado' : 'Pegar' }}
            </button>
            <BaseSegmented
              v-model="form.template_style"
              size="sm"
              :options="templateStyleOptions"
              aria-label="Estilo de plantilla"
            />
            <BaseButton variant="secondary" size="sm" :disabled="!form.content_markdown.trim()" @click="showFullPreview = true">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
              Vista completa
            </BaseButton>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors"
              :class="showPreview
                ? 'bg-primary-soft text-text-brand hover:bg-primary-soft'
                : 'bg-surface-raised text-text-muted hover:bg-surface-raised'"
              @click="showPreview = !showPreview"
            >
              <svg v-if="showPreview" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
              </svg>
              {{ showPreview ? 'Ocultar vista previa' : 'Vista previa' }}
            </button>
          </div>
        </div>
        <div :class="showPreview ? 'grid grid-cols-1 panel-desktop:grid-cols-2 gap-4 flex-1 min-h-0' : 'flex-1 min-h-0 flex'">
          <textarea
            id="edit-markdown"
            ref="markdownTextareaRef"
            v-model="form.content_markdown"
            placeholder="# Contenido del documento..."
            class="w-full px-4 py-3 border border-border-default rounded-xl text-sm font-mono leading-relaxed bg-surface text-text-default placeholder:text-text-subtle
                   focus:ring-2 focus:ring-focus-ring/30 focus:border-focus-ring outline-none resize-none
                   min-h-[24rem] panel-desktop:h-[calc(100vh-18rem)]"
          ></textarea>
          <div
            v-if="showPreview"
            class="border border-border-default rounded-xl bg-surface overflow-y-auto
                   min-h-[24rem] panel-desktop:h-[calc(100vh-18rem)]"
          >
            <div class="sticky top-0 px-3 py-2 border-b border-border-default bg-surface-raised rounded-t-xl z-10">
              <span class="text-xs font-medium text-text-muted uppercase tracking-wide">Vista previa</span>
            </div>
            <DocumentMarkdownBody
              v-if="form.content_markdown.trim()"
              :markdown="form.content_markdown"
              :theme="form.template_style"
              class="px-5 py-4"
            />
            <div
              v-else
              class="flex items-center justify-center h-64 text-sm text-text-subtle"
            >
              Escribe markdown para ver la vista previa...
            </div>
          </div>
        </div>

        <div class="mt-5 flex flex-wrap items-center gap-3 panel-landscape:hidden">
          <BaseButton
            variant="primary"
            size="md"
            type="submit"
            class="sm:px-6"
            data-testid="doc-save-mobile"
            :disabled="documentStore.isUpdating || !hasChanges || lockedCuenta"
          >
            {{ documentStore.isUpdating ? 'Guardando...' : (hasChanges ? 'Guardar cambios' : 'Guardar') }}
          </BaseButton>
          <BaseDropdown :items="downloadItems" align="right">
            <template #trigger>
              <BaseButton variant="secondary" size="md" class="sm:px-6" :disabled="isDownloading">
                {{ isDownloading ? 'Descargando...' : 'Descargar PDF' }}
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </BaseButton>
            </template>
          </BaseDropdown>
          <NuxtLink :to="localePath('/panel/documents')" class="text-sm text-text-muted hover:text-text-default">
            Cancelar
          </NuxtLink>
        </div>
      </section>
    </form>

    <DocumentClientNoteModal
      v-model="showClientNote"
      :subject="form.client_email_subject"
      :email-body="form.client_email_body"
      :whatsapp-message="form.client_whatsapp_message"
      :custom-notes="form.client_custom_notes"
      :readonly="lockedCuenta"
      :saving="documentStore.isUpdating"
      @submit="saveClientNote"
    />

    <MarkdownPreviewModal
      v-model="showFullPreview"
      :title="form.title || 'Vista previa'"
    >
      <DocumentMarkdownBody
        v-if="form.content_markdown.trim()"
        :markdown="form.content_markdown"
        variant="full"
        :theme="form.template_style"
        class="max-w-4xl mx-auto"
      />
      <div v-else class="flex items-center justify-center h-full text-sm text-text-subtle">
        No hay contenido para mostrar.
      </div>
    </MarkdownPreviewModal>

    <!-- El PDF de verdad, el mismo que entrega la descarga: es lo único que
         muestra las portadas, que la vista previa de markdown no rinde. -->
    <DocumentPdfPreviewModal
      v-model="showPdfPreview"
      :document-id="route.params.id"
      :title="form.title || 'Vista previa del PDF'"
      :template-style="form.template_style"
      :version="documentStore.currentDocument?.updated_at || ''"
      :cover-options="savedCoverOptions"
    />

    <!-- Las tres salidas del guard: [Seguir editando] [Salir sin guardar]
         [Guardar y salir]. Sin este modal el guard abriría un diálogo que
         nadie renderiza y la navegación se bloquearía en silencio. -->
    <ConfirmModal
      v-model="confirmState.open"
      :title="confirmState.title"
      :message="confirmState.message"
      :confirm-text="confirmState.confirmText"
      :cancel-text="confirmState.cancelText"
      :variant="confirmState.variant"
      :require-type-text="confirmState.requireTypeText"
      :hide-cancel="confirmState.hideCancel"
      :secondary-text="confirmState.secondaryText"
      :secondary-variant="confirmState.secondaryVariant"
      :secondary-hint="confirmState.secondaryHint"
      :loading="confirmState.busy"
      @confirm="handleConfirmed"
      @secondary="handleSecondaryAction"
      @cancel="handleCancelled"
    />
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, nextTick } from 'vue';
import TagSelector from '~/components/panel/documents/TagSelector.vue';
import MarkdownPreviewModal from '~/components/panel/documents/MarkdownPreviewModal.vue';
import DocumentPdfPreviewModal from '~/components/panel/documents/DocumentPdfPreviewModal.vue';
import DocumentMarkdownBody from '~/components/panel/documents/DocumentMarkdownBody.vue';
import DocumentClientNoteModal from '~/components/panel/documents/DocumentClientNoteModal.vue';
import ClientAutocomplete from '~/components/ui/ClientAutocomplete.vue';
import ProjectSelect from '~/components/accounting/ProjectSelect.vue';
import ClientFormFields from '~/components/clients/ClientFormFields.vue';
import UnsavedChangesNotice from '~/components/panel/UnsavedChangesNotice.vue';
import { clientFormPayload, emptyClientForm } from '~/utils/billingCode';
import { useProposalClientsStore } from '~/stores/proposal_clients';
import { useClientProjectCascade } from '~/composables/useClientProjectCascade';
import { usePanelRefresh } from '~/composables/usePanelRefresh';
import { usePanelNotify } from '~/composables/usePanelNotify';
import { useUnsavedGuard } from '~/composables/useUnsavedGuard';
import { joinEs } from '~/utils/spanishList';
import { describeIncludedPages } from '~/utils/documentCoverPages';

const localePath = useLocalePath();
const route = useRoute();
definePageMeta({ layout: 'admin', middleware: ['admin-auth'] });

const documentStore = useDocumentStore();
const folderStore = useDocumentFolderStore();
const tagStore = useDocumentTagStore();
const clientsStore = useProposalClientsStore();
const notify = usePanelNotify();
const loadError = ref(false);
// Requisito 6: an issued cuenta is a fact — read-only here, forever.
const lockedCuenta = ref(false);
const clientDisplayName = ref('');
// El nombre libre heredado sigue existiendo (lo lee el PDF); se muestra como
// referencia mientras el documento no tenga cliente relacional.
const legacyClientName = ref('');
const inlineClientOpen = ref(false);
const inlineClient = ref(emptyClientForm());
const creatingClient = ref(false);
// Los enlaces apuntan a lo GUARDADO, no a una selección sin guardar.
const savedClientId = ref(null);
const savedClientLabel = ref('');
const savedProjectId = ref(null);
const savedProjectName = ref('');
const isDownloading = ref(false);
const showPreview = ref(true);
const showFullPreview = ref(false);
const showPdfPreview = ref(false);
const showClientNote = ref(false);
const copiedMarkdown = ref(false);
const pastedMarkdown = ref(false);
const markdownTextareaRef = ref(null);

const form = reactive({
  title: '',
  client: null,
  project: null,
  language: 'es',
  include_portada: true,
  include_subportada: true,
  include_contraportada: true,
  status: 'draft',
  content_markdown: '',
  client_email_subject: '',
  client_email_body: '',
  client_whatsapp_message: '',
  client_custom_notes: [],
  folder_id: null,
  tag_ids: [],
  template_style: 'professional',
});

// Nombres sin artículo: se encadenan como los encadenaría una persona
// ("cliente y proyecto sin guardar").
const FIELD_LABELS = {
  title: 'título',
  client: 'cliente',
  project: 'proyecto',
  language: 'idioma',
  include_portada: 'portada',
  include_subportada: 'subportada',
  include_contraportada: 'contraportada',
  status: 'estado',
  content_markdown: 'contenido',
  client_email_subject: 'asunto del correo',
  client_email_body: 'correo para el cliente',
  client_whatsapp_message: 'WhatsApp para el cliente',
  client_custom_notes: 'notas adicionales',
  folder_id: 'carpeta',
  tag_ids: 'etiquetas',
  template_style: 'estilo de plantilla',
};

const NOTE_FIELDS = [
  'client_email_subject',
  'client_email_body',
  'client_whatsapp_message',
  'client_custom_notes',
];

// Se desestructura para que los refs queden como bindings de primer nivel: a
// través del objeto (`guard.hasChanges`) el template no los desenvuelve.
const {
  hasChanges,
  isFieldDirty,
  dirtyLabels,
  unsavedTitle,
  unsavedDetail,
  canSaveNow,
  commit: commitBaseline,
  guardedReload,
  guardedExport,
  discardChanges,
  confirmState,
  handleConfirmed,
  handleSecondaryAction,
  handleCancelled,
} = useUnsavedGuard({
  snapshot: () => ({ ...form, tag_ids: [...form.tag_ids] }),
  labels: FIELD_LABELS,
  save: handleSave,
  // Una cuenta de cobro emitida no se guarda: el backend contesta 400
  // collection_account_locked. Ofrecer "Guardar y salir" ahí sería mentir.
  canSave: () => !lockedCuenta.value,
  blockedReason: 'Esta cuenta de cobro ya fue emitida y no se puede modificar.',
  reload: reloadDocument,
});

const headerClientLabel = computed(() => clientDisplayName.value || legacyClientName.value);

const hasNotes = computed(() => [
  form.client_email_subject,
  form.client_email_body,
  form.client_whatsapp_message,
].some((value) => value.trim()) || form.client_custom_notes.length > 0);

const notesActionLabel = computed(() => (
  hasNotes.value ? 'Editar notas' : 'Agregar notas'
));

const notesDirty = computed(() => NOTE_FIELDS.some((field) => isFieldDirty(field)));

function assignClientNote(note) {
  form.client_email_subject = note.subject;
  form.client_email_body = note.emailBody;
  form.client_whatsapp_message = note.whatsappMessage;
  form.client_custom_notes = note.customNotes;
}

function notePayload(note) {
  return {
    client_email_subject: note.subject,
    client_email_body: note.emailBody,
    client_whatsapp_message: note.whatsappMessage,
    client_custom_notes: note.customNotes,
  };
}

function notifySaveError(result, title = 'No se pudo guardar el documento') {
  if (result.code === 'collection_account_locked') {
    lockedCuenta.value = true;
    notify.error({ title: 'Documento emitido', detail: result.message });
    return;
  }
  const fieldDetail = result.fieldErrors
    ? Object.entries(result.fieldErrors).map(([key, value]) => `${key}: ${value}`).join(' · ')
    : '';
  notify.error({
    title,
    detail: fieldDetail || result.message,
  });
}

async function saveClientNote(note) {
  const result = await documentStore.updateDocument(route.params.id, notePayload(note));
  if (!result.success) {
    notifySaveError(result, 'No se pudieron guardar las notas');
    return;
  }
  assignClientNote(note);
  commitBaseline(NOTE_FIELDS);
  showClientNote.value = false;
  notify.success({
    title: 'Notas guardadas',
    detail: 'Los cambios quedaron guardados en el documento.',
    duration: 6000,
  });
}

const { onClientSelect, onProjectSelect } = useClientProjectCascade(
  form,
  clientDisplayName,
);

function onCreateNewClient(typedName) {
  inlineClientOpen.value = true;
  inlineClient.value = { ...emptyClientForm(), name: typedName || '' };
}

async function createInlineClient() {
  creatingClient.value = true;
  const result = await clientsStore.createClient(clientFormPayload(inlineClient.value));
  creatingClient.value = false;
  if (result.success && result.data?.id) {
    inlineClientOpen.value = false;
    onClientSelect(result.data);
  }
}

function applyAssociationSnapshot(data) {
  savedClientId.value = data.client ?? null;
  savedClientLabel.value = data.client_display_name || '';
  savedProjectId.value = data.project ?? null;
  savedProjectName.value = data.project_name || '';
  legacyClientName.value = data.client_name || '';
}

const coverOptions = [
  { key: 'include_portada', label: 'Incluir portada', testId: 'doc-cover-portada' },
  { key: 'include_subportada', label: 'Incluir subportada', testId: 'doc-cover-subportada' },
  { key: 'include_contraportada', label: 'Incluir contraportada', testId: 'doc-cover-contraportada' },
];

// Las casillas dicen qué se incluye; esto dice qué va a salir, en el orden en
// que sale. Se lee del formulario vivo, así el efecto de desmarcar una casilla
// se ve antes de guardar (el PDF, en cambio, se arma con lo guardado).
const includedPagesLabel = computed(() => describeIncludedPages(form));

// La vista previa muestra el PDF GUARDADO: su encabezado tiene que describir
// esa configuración, no la de la pantalla, o volvería a prometer algo que el
// archivo no cumple.
const savedCoverOptions = computed(() => {
  const saved = documentStore.currentDocument || {};
  return {
    include_portada: saved.include_portada,
    include_subportada: saved.include_subportada,
    include_contraportada: saved.include_contraportada,
  };
});

const templateStyleOptions = [
  { value: 'friendly', label: 'Amigable', testId: 'doc-style-friendly' },
  { value: 'professional', label: 'Profesional', testId: 'doc-style-professional' },
];

// Sin 'archived': "Archivado" es ahora el estado que saca el documento de la
// vista (acción Archivar), no un estado editorial homónimo que no ocultaba nada.
const statusOptions = [
  { value: 'draft', label: 'Borrador' },
  { value: 'published', label: 'Publicado' },
];

const statusLabel = computed(
  () => statusOptions.find((option) => option.value === form.status)?.label || '',
);

async function handleCopyContent() {
  try {
    await navigator.clipboard.writeText(form.content_markdown);
    copiedMarkdown.value = true;
    setTimeout(() => { copiedMarkdown.value = false; }, 2000);
  } catch {
    notify.error({
      title: 'No se pudo copiar al portapapeles',
      detail: 'Tu navegador bloqueó el acceso al portapapeles.',
    });
  }
}

async function handlePasteContent() {
  try {
    const pasted = await navigator.clipboard.readText();
    if (!pasted) return;
    const textarea = markdownTextareaRef.value;
    const start = textarea ? textarea.selectionStart : form.content_markdown.length;
    const end = textarea ? textarea.selectionEnd : form.content_markdown.length;
    form.content_markdown = form.content_markdown.slice(0, start) + pasted + form.content_markdown.slice(end);
    const cursor = start + pasted.length;
    if (textarea) {
      nextTick(() => {
        textarea.focus();
        textarea.setSelectionRange(cursor, cursor);
      });
    }
    pastedMarkdown.value = true;
    setTimeout(() => { pastedMarkdown.value = false; }, 2000);
  } catch {
    notify.error({
      title: 'No se pudo pegar desde el portapapeles',
      detail: 'Tu navegador bloqueó el acceso al portapapeles.',
    });
  }
}

async function handleUnarchive() {
  const id = documentStore.currentDocument?.id;
  if (!id) return;
  const result = await documentStore.unarchiveDocument(id);
  if (result.success) {
    notify.success({ title: 'Documento restaurado' });
    await documentStore.fetchDocument(id);
  } else {
    notify.error({ title: 'No se pudo restaurar el documento', detail: result.message });
  }
}

async function reloadDocument() {
  const id = route.params.id;
  loadError.value = false;
  const [result] = await Promise.all([
    documentStore.fetchDocument(id),
    folderStore.fetchFolders(),
    tagStore.fetchTags(),
  ]);
  if (result.success && result.data) {
    form.title = result.data.title || '';
    form.client = result.data.client ?? null;
    form.project = result.data.project ?? null;
    clientDisplayName.value = result.data.client_display_name || '';
    applyAssociationSnapshot(result.data);
    form.language = result.data.language || 'es';
    form.include_portada = result.data.include_portada !== undefined ? result.data.include_portada : true;
    form.include_subportada = result.data.include_subportada !== undefined ? result.data.include_subportada : true;
    form.include_contraportada = result.data.include_contraportada !== undefined ? result.data.include_contraportada : true;
    form.status = result.data.status || 'draft';
    form.content_markdown = result.data.content_markdown || '';
    form.client_email_subject = result.data.client_email_subject || '';
    form.client_email_body = result.data.client_email_body || '';
    form.client_whatsapp_message = result.data.client_whatsapp_message || '';
    form.client_custom_notes = Array.isArray(result.data.client_custom_notes)
      ? result.data.client_custom_notes.map((note) => ({ ...note }))
      : [];
    form.folder_id = result.data.folder || null;
    form.tag_ids = Array.isArray(result.data.tag_ids) ? [...result.data.tag_ids] : [];
    form.template_style = result.data.template_style || 'professional';
    lockedCuenta.value = (
      result.data.document_type_code === 'collection_account'
      && result.data.commercial_status !== 'draft'
    );
    commitBaseline();
  } else {
    loadError.value = true;
  }
}

onMounted(reloadDocument);
// El refresh global vuelve a pedir el documento y pisa el formulario sin
// avisar: se registra la versión que pregunta primero. `onMounted` y el botón
// "Reintentar" siguen llamando al crudo — ahí no hay nada que perder.
usePanelRefresh(guardedReload);

async function handleSave() {
  const payload = {
    title: form.title.trim(),
    // Siempre presentes, null incluido: es lo que permite desvincular.
    client: form.client ?? null,
    project: form.project ?? null,
    language: form.language,
    include_portada: form.include_portada,
    include_subportada: form.include_subportada,
    include_contraportada: form.include_contraportada,
    status: form.status,
    content_markdown: form.content_markdown,
    client_email_subject: form.client_email_subject,
    client_email_body: form.client_email_body,
    client_whatsapp_message: form.client_whatsapp_message,
    client_custom_notes: form.client_custom_notes,
    folder_id: form.folder_id,
    tag_ids: form.tag_ids,
    template_style: form.template_style,
  };

  // Se capturan ANTES de guardar: guardar limpia la lista.
  const savedLabels = [...dirtyLabels.value];

  const result = await documentStore.updateDocument(route.params.id, payload);
  if (result.success) {
    commitBaseline();
    if (result.data) {
      applyAssociationSnapshot(result.data);
      clientDisplayName.value = result.data.client_display_name || clientDisplayName.value;
    }
    // Confirmar QUÉ se guardó, no sólo que algo se guardó: sin eso la duda
    // pasa al otro lado —no se sabe si guardó o si el aviso sólo desapareció—.
    notify.success({
      title: 'Documento guardado',
      detail: savedLabels.length ? `Se guardó: ${joinEs(savedLabels)}.` : '',
      duration: 6000,
    });
    return true;
  }
  // The server is the truth: the cuenta may have been issued in another tab.
  notifySaveError(result);
  // Sin re-fijar la baseline a propósito: un guardado fallido deja el aviso
  // puesto y, desde el guard de salida, bloquea la navegación.
  return false;
}

const downloadItems = computed(() => [
  { label: 'Descargar · Amigable', onClick: () => handleDownloadPdf('friendly') },
  { label: 'Descargar · Profesional', onClick: () => handleDownloadPdf('professional') },
]);

async function handleDownloadPdf(template = null) {
  // El archivo lo arma el servidor con lo guardado: con cambios en pantalla
  // hay que decidir primero cuál de las dos versiones se descarga.
  if (!(await guardedExport('download'))) return;
  isDownloading.value = true;
  const result = await documentStore.downloadPdf(
    route.params.id, form.title || 'document', template);
  isDownloading.value = false;
  if (!result.success) {
    notify.error({ title: 'No se pudo descargar el PDF', detail: result.message });
  }
}

async function handlePreviewPdf() {
  if (!(await guardedExport('preview'))) return;
  showPdfPreview.value = true;
}
</script>
