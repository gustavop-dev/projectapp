import { computed, onMounted, ref, unref } from 'vue'
import { get_request } from '~/stores/services/request_http'
import { downloadBlob, filenameFromDisposition } from '~/utils/downloadFile'

const PRODUCTION_ORIGIN = 'https://projectapp.co'

export function useAdditionalModulesPublicAccess(language) {
  const origin = ref(PRODUCTION_ORIGIN)
  const isDownloading = ref(false)

  const normalizedLanguage = computed(() => (unref(language) === 'en' ? 'en' : 'es'))
  const localeSegment = computed(() => (
    normalizedLanguage.value === 'en' ? 'en-us' : 'es-co'
  ))
  const publicPath = computed(() => `/${localeSegment.value}/additional-modules`)
  const publicUrl = computed(() => `${origin.value}${publicPath.value}`)
  const pdfUrl = computed(() => (
    `${origin.value}/api/additional-modules/public/pdf/?lang=${normalizedLanguage.value}`
  ))

  onMounted(() => {
    if (typeof window !== 'undefined' && window.location?.origin) {
      origin.value = window.location.origin
    }
  })

  async function copyPublicUrl() {
    if (typeof navigator === 'undefined' || !navigator.clipboard?.writeText) return false

    try {
      await navigator.clipboard.writeText(publicUrl.value)
      return true
    } catch {
      return false
    }
  }

  async function downloadFullPdf() {
    if (isDownloading.value) return false

    isDownloading.value = true
    try {
      const response = await get_request(
        `additional-modules/public/pdf/?lang=${normalizedLanguage.value}`,
        { responseType: 'blob' },
      )
      const fallbackFilename = normalizedLanguage.value === 'en'
        ? 'additional-modules-catalog.pdf'
        : 'catalogo-modulos-adicionales.pdf'
      const filename = filenameFromDisposition(
        response.headers?.['content-disposition'],
      ) || fallbackFilename

      downloadBlob(response.data, filename)
      return true
    } catch {
      return false
    } finally {
      isDownloading.value = false
    }
  }

  return {
    publicPath,
    publicUrl,
    pdfUrl,
    isDownloading,
    copyPublicUrl,
    downloadFullPdf,
  }
}
