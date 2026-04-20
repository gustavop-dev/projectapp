<template>
  <div id="platform-deliverable-detail" class="pb-12">
    <div v-if="isLoading" class="py-20 text-center">
      <div class="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-esmerald/20 border-t-esmerald dark:border-white/20 dark:border-t-lemon" />
    </div>

    <template v-else-if="detail">
      <div class="mb-6" data-enter>
        <NuxtLink
          :to="localePath(`/platform/projects/${projectId}/deliverables`)"
          class="mb-2 inline-flex items-center gap-1.5 text-sm text-green-light transition hover:text-esmerald dark:hover:text-white"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" /></svg>
          Entregables
        </NuxtLink>
        <h1 class="text-xl font-bold text-esmerald dark:text-white sm:text-2xl">{{ detail.title }}</h1>
        <p v-if="detail.description" class="mt-2 max-w-2xl text-sm text-green-light">{{ detail.description }}</p>
        <div v-if="detail.source_epic_key" class="mt-2 text-xs text-green-light/70">
          Módulo: {{ detail.source_epic_title || detail.source_epic_key }}
        </div>
      </div>

      <div class="mb-8 grid gap-4 lg:grid-cols-2" data-enter>
        <div class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald">
          <h2 class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">Documentos</h2>

          <div v-if="detail.has_business_proposal" class="space-y-2">
            <p class="text-sm font-medium text-esmerald dark:text-white">{{ detail.proposal_title }}</p>
            <p class="text-xs text-green-light">Propuesta comercial vinculada a este entregable.</p>
            <div class="flex flex-wrap gap-2">
              <button
                type="button"
                class="rounded-xl border border-esmerald/15 px-3 py-2 text-xs font-medium text-esmerald transition hover:bg-esmerald-light/40 dark:border-white/15 dark:text-lemon dark:hover:bg-white/[0.06]"
                @click="downloadPdf('commercial')"
              >
                PDF comercial
              </button>
              <button
                type="button"
                class="rounded-xl border border-esmerald/15 px-3 py-2 text-xs font-medium text-esmerald transition hover:bg-esmerald-light/40 dark:border-white/15 dark:text-lemon dark:hover:bg-white/[0.06]"
                @click="downloadPdf('technical')"
              >
                PDF técnico
              </button>
            </div>
          </div>
          <p v-else class="text-sm text-green-light">No hay propuesta comercial en este entregable.</p>

          <div v-if="detail.file_url" class="mt-4 border-t border-esmerald/[0.06] pt-4 dark:border-white/[0.06]">
            <p class="mb-2 text-xs font-medium text-green-light/60">Archivo principal</p>
            <a
              :href="detail.file_url"
              target="_blank"
              rel="noopener"
              class="inline-flex items-center gap-2 text-sm font-medium text-esmerald dark:text-lemon"
            >
              {{ detail.file_name || 'Descargar' }}
            </a>
          </div>

          <div v-if="detail.attachment_files?.length" class="mt-4 border-t border-esmerald/[0.06] pt-4 dark:border-white/[0.06]">
            <p class="mb-2 text-xs font-medium text-green-light/60">Archivos adicionales</p>
            <ul class="space-y-2">
              <li v-for="f in detail.attachment_files" :key="f.id">
                <a
                  v-if="f.file_url"
                  :href="f.file_url"
                  target="_blank"
                  rel="noopener"
                  class="text-sm text-esmerald dark:text-lemon"
                >
                  {{ f.title || f.file_url.split('/').pop() }}
                </a>
              </li>
            </ul>
          </div>

          <form v-if="authStore.isAdmin" class="mt-4 border-t border-esmerald/[0.06] pt-4 dark:border-white/[0.06]" @submit.prevent="uploadAttachment">
            <p class="mb-2 text-xs font-medium text-green-light/60">Subir anexo (admin)</p>
            <div class="flex flex-col gap-2 sm:flex-row sm:items-end">
              <input v-model="attachTitle" type="text" placeholder="Título opcional" class="rounded-xl border border-esmerald/10 bg-esmerald-light/30 px-3 py-2 text-sm dark:border-white/10 dark:bg-esmerald-dark dark:text-white" />
              <select v-model="attachCategory" class="rounded-xl border border-esmerald/10 bg-esmerald-light/30 px-3 py-2 text-sm dark:border-white/10 dark:bg-esmerald-dark dark:text-white">
                <option value="contract">Contrato</option>
                <option value="amendment">Otrosí</option>
                <option value="legal_annex">Anexo legal</option>
                <option value="documents">Documentos</option>
                <option value="other">Otros</option>
              </select>
              <input ref="attachInput" type="file" class="text-xs text-green-light" @change="onAttachFile" />
              <button type="submit" :disabled="!attachFile || attachUploading" class="rounded-xl bg-lemon px-4 py-2 text-xs font-semibold text-esmerald-dark disabled:opacity-50">
                {{ attachUploading ? '…' : 'Subir' }}
              </button>
            </div>
          </form>

          <div class="mt-4 border-t border-esmerald/[0.06] pt-4 dark:border-white/[0.06]">
            <p class="mb-2 text-xs font-medium text-green-light/60">Tus PDF (cliente)</p>
            <p class="mb-2 text-xs text-green-light/80">Solo archivos PDF. Puedes usar una carpeta opcional para organizarlos.</p>
            <ul v-if="detail.client_uploads?.length" class="mb-3 space-y-1">
              <li v-for="u in detail.client_uploads" :key="u.id">
                <a
                  v-if="u.file_url"
                  :href="u.file_url"
                  target="_blank"
                  rel="noopener"
                  class="text-sm text-esmerald dark:text-lemon"
                >
                  {{ u.title || u.file_name || 'PDF' }}
                </a>
              </li>
            </ul>
            <form class="flex flex-col gap-2" @submit.prevent="createClientFolder">
              <div class="flex flex-wrap gap-2">
                <input
                  v-model="newFolderName"
                  type="text"
                  placeholder="Nombre de carpeta (opcional)"
                  class="min-w-[10rem] flex-1 rounded-xl border border-esmerald/10 bg-esmerald-light/30 px-3 py-2 text-sm dark:border-white/10 dark:bg-esmerald-dark dark:text-white"
                />
                <button type="submit" class="rounded-xl border border-esmerald/15 px-3 py-2 text-xs font-medium text-esmerald dark:border-white/15 dark:text-lemon">
                  Crear carpeta
                </button>
              </div>
            </form>
            <form class="mt-3 flex flex-col gap-2 sm:flex-row sm:items-end" @submit.prevent="uploadClientPdf">
              <select
                v-model="clientPdfFolderId"
                class="rounded-xl border border-esmerald/10 bg-esmerald-light/30 px-3 py-2 text-sm dark:border-white/10 dark:bg-esmerald-dark dark:text-white"
              >
                <option value="">Sin carpeta</option>
                <option v-for="f in detail.client_folders" :key="f.id" :value="String(f.id)">{{ f.name }}</option>
              </select>
              <input v-model="clientPdfTitle" type="text" placeholder="Título opcional" class="rounded-xl border border-esmerald/10 bg-esmerald-light/30 px-3 py-2 text-sm dark:border-white/10 dark:bg-esmerald-dark dark:text-white" />
              <input ref="clientPdfInput" type="file" accept=".pdf,application/pdf" class="text-xs text-green-light" @change="onClientPdfFile" />
              <button type="submit" :disabled="!clientPdfFile || clientPdfUploading" class="rounded-xl bg-esmerald px-4 py-2 text-xs font-semibold text-white disabled:opacity-50 dark:bg-lemon dark:text-esmerald-dark">
                {{ clientPdfUploading ? '…' : 'Subir PDF' }}
              </button>
            </form>
          </div>

          <div v-if="detail.collection_accounts?.length" class="mt-4 border-t border-esmerald/[0.06] pt-4 dark:border-white/[0.06]">
            <p class="mb-2 text-xs font-medium text-green-light/60">Cuentas de cobro</p>
            <ul class="space-y-2">
              <li v-for="ca in detail.collection_accounts" :key="ca.id" class="flex flex-wrap items-center gap-2 text-sm">
                <span class="font-medium text-esmerald dark:text-white">{{ ca.title }}</span>
                <span class="text-xs text-green-light">{{ ca.public_number }}</span>
                <span class="text-xs uppercase text-green-light/70">{{ ca.commercial_status }}</span>
                <button
                  type="button"
                  class="text-xs text-lemon underline"
                  @click="downloadCollectionPdf(ca.id)"
                >
                  PDF
                </button>
              </li>
            </ul>
            <NuxtLink
              :to="localePath({ path: `/platform/projects/${projectId}/collection-accounts`, query: { deliverable_id: deliverableId } })"
              class="mt-2 inline-block text-xs text-green-light underline"
            >
              Ver todas las cuentas del proyecto
            </NuxtLink>
          </div>
        </div>

        <div class="rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald">
          <h2 class="mb-3 text-xs font-semibold uppercase tracking-wider text-green-light/60">Requerimientos</h2>
          <p class="mb-4 text-sm text-green-light">
            Tablero Kanban filtrado a tarjetas de este entregable.
          </p>
          <NuxtLink
            :to="localePath({ path: `/platform/projects/${projectId}/board`, query: { deliverable_id: deliverableId } })"
            class="inline-flex items-center gap-2 rounded-xl bg-esmerald px-4 py-2.5 text-sm font-semibold text-white dark:bg-lemon dark:text-esmerald-dark"
          >
            Abrir tablero
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
          </NuxtLink>
        </div>
      </div>

      <div
        v-if="detail.data_model_entities?.length"
        class="mb-8 rounded-2xl border border-esmerald/[0.06] bg-white p-5 dark:border-white/[0.06] dark:bg-esmerald"
        data-enter
      >
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wider text-green-light/60">Modelo de datos</h2>
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="entity in detail.data_model_entities"
            :key="entity.id"
            class="rounded-xl border border-esmerald/[0.06] p-4 dark:border-white/[0.06]"
          >
            <h3 class="text-sm font-semibold text-esmerald dark:text-white">{{ entity.name }}</h3>
            <p v-if="entity.description" class="mt-1 text-xs text-green-light">{{ entity.description }}</p>
            <div v-if="entity.key_fields" class="mt-2">
              <span class="text-[10px] font-medium uppercase tracking-wider text-green-light/50">Campos clave</span>
              <div class="mt-1 flex flex-wrap gap-1">
                <span
                  v-for="field in entity.key_fields.split(',')"
                  :key="field.trim()"
                  class="rounded-md bg-esmerald-light/30 px-2 py-0.5 text-[11px] font-medium text-esmerald dark:bg-white/[0.06] dark:text-lemon"
                >
                  {{ field.trim() }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="py-16 text-center text-sm text-green-light">
      Entregable no encontrado.
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { usePageEntrance } from '~/composables/usePageEntrance'
import { usePlatformApi } from '~/composables/usePlatformApi'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformProjectsStore } from '~/stores/platform-projects'

definePageMeta({ layout: 'platform', middleware: ['platform-auth'] })
usePageEntrance('#platform-deliverable-detail')

const route = useRoute()
const localePath = useLocalePath()
const authStore = usePlatformAuthStore()
const projectsStore = usePlatformProjectsStore()

const projectId = computed(() => route.params.id)
const deliverableId = computed(() => route.params.deliverableId)

const detail = ref(null)
const isLoading = ref(true)
const attachTitle = ref('')
const attachCategory = ref('documents')
const attachFile = ref(null)
const attachInput = ref(null)
const attachUploading = ref(false)

const newFolderName = ref('')
const clientPdfFolderId = ref('')
const clientPdfTitle = ref('')
const clientPdfFile = ref(null)
const clientPdfInput = ref(null)
const clientPdfUploading = ref(false)

function onAttachFile(e) {
  const f = e.target.files?.[0]
  attachFile.value = f || null
}

async function load() {
  isLoading.value = true
  detail.value = null
  try {
    await projectsStore.fetchProject(projectId.value)
    const { get } = usePlatformApi()
    const res = await get(
      `projects/${projectId.value}/deliverables/${deliverableId.value}/`,
    )
    detail.value = res.data
  } catch {
    detail.value = null
  } finally {
    isLoading.value = false
  }
}

async function downloadPdf(kind) {
  const paths = detail.value?.pdf_download_paths
  if (!paths) return
  const rel = kind === 'technical' ? paths.technical : paths.commercial
  try {
    const { get } = usePlatformApi()
    const res = await get(rel, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = kind === 'technical' ? 'technical.pdf' : 'proposal.pdf'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    // eslint-disable-next-line no-alert
    alert('No se pudo descargar el PDF.')
  }
}

function onClientPdfFile(e) {
  const f = e.target.files?.[0]
  clientPdfFile.value = f || null
}

async function createClientFolder() {
  const name = newFolderName.value.trim()
  if (!name) return
  try {
    const { post } = usePlatformApi()
    await post(
      `projects/${projectId.value}/deliverables/${deliverableId.value}/client-folders/`,
      { name, order: 0 },
    )
    newFolderName.value = ''
    await load()
  } catch {
    // eslint-disable-next-line no-alert
    alert('No se pudo crear la carpeta.')
  }
}

async function uploadClientPdf() {
  if (!clientPdfFile.value) return
  clientPdfUploading.value = true
  try {
    const { post } = usePlatformApi()
    const fd = new FormData()
    fd.append('file', clientPdfFile.value)
    if (clientPdfTitle.value.trim()) fd.append('title', clientPdfTitle.value.trim())
    const fid = clientPdfFolderId.value ? Number(clientPdfFolderId.value) : null
    if (fid) fd.append('folder_id', String(fid))
    await post(
      `projects/${projectId.value}/deliverables/${deliverableId.value}/client-uploads/`,
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    clientPdfTitle.value = ''
    clientPdfFile.value = null
    if (clientPdfInput.value) clientPdfInput.value.value = ''
    await load()
  } catch {
    // eslint-disable-next-line no-alert
    alert('Solo PDF permitido o archivo demasiado grande.')
  } finally {
    clientPdfUploading.value = false
  }
}

async function downloadCollectionPdf(accountId) {
  try {
    const { get } = usePlatformApi()
    const res = await get(`collection-accounts/${accountId}/pdf/`, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cuenta-${accountId}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    // eslint-disable-next-line no-alert
    alert('No se pudo descargar el PDF.')
  }
}

async function uploadAttachment() {
  if (!attachFile.value) return
  attachUploading.value = true
  try {
    const { post } = usePlatformApi()
    const fd = new FormData()
    fd.append('file', attachFile.value)
    fd.append('title', attachTitle.value)
    fd.append('category', attachCategory.value)
    await post(
      `projects/${projectId.value}/deliverables/${deliverableId.value}/attachments/`,
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    attachTitle.value = ''
    attachFile.value = null
    if (attachInput.value) attachInput.value.value = ''
    await load()
  } catch {
    // eslint-disable-next-line no-alert
    alert('Error al subir el archivo.')
  } finally {
    attachUploading.value = false
  }
}

onMounted(load)

</script>
