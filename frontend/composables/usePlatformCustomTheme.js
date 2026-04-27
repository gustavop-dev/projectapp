import { ref, computed } from 'vue'
import { usePlatformAuthStore } from '~/stores/platform-auth'
import { usePlatformApi } from '~/composables/usePlatformApi'
import { hexToRgb, luminance, toRgbString, measureBrightness } from '~/utils/colorUtils'

const THEME_COLORS = [
  { name: 'Esmerald', shades: ['#e6efef', '#ccdedd', '#99bdbc', '#669c9a', '#337b79', '#002921', '#00231c', '#001d17', '#001713'] },
  { name: 'Blue', shades: ['#e8f0fe', '#c5d9fc', '#91b8f9', '#5c96f6', '#2874f3', '#0b57d0', '#094ab0', '#073d90', '#053070'] },
  { name: 'Purple', shades: ['#f3e8fd', '#e0c6fb', '#c48df7', '#a854f3', '#8c1bef', '#7b1fa2', '#6a1b8a', '#591672', '#48115a'] },
  { name: 'Pink', shades: ['#fde8f0', '#fac6d9', '#f58db8', '#f05497', '#eb1b76', '#c2185b', '#a3144d', '#85103f', '#660c30'] },
  { name: 'Red', shades: ['#fde8e8', '#fac6c6', '#f58d8d', '#f05454', '#eb1b1b', '#c62828', '#a82222', '#8a1c1c', '#6b1515'] },
  { name: 'Orange', shades: ['#fff3e0', '#ffe0b2', '#ffcc80', '#ffb74d', '#ffa726', '#ef6c00', '#cc5c00', '#a84c00', '#853d00'] },
  { name: 'Yellow', shades: ['#fffde7', '#fff9c4', '#fff59d', '#fff176', '#ffee58', '#f9a825', '#d48f20', '#af761a', '#8a5d15'] },
  { name: 'Green', shades: ['#e8f5e9', '#c8e6c9', '#a5d6a7', '#81c784', '#66bb6a', '#2e7d32', '#27692a', '#205623', '#19431b'] },
  { name: 'Teal', shades: ['#e0f2f1', '#b2dfdb', '#80cbc4', '#4db6ac', '#26a69a', '#00796b', '#00675b', '#00554b', '#00433b'] },
]

const themeColor = ref('')
const coverImage = ref('')
const customCoverImageUrl = ref('')
const coverDark = ref(false)
let initialized = false

function findColorFamily(hex) {
  for (const family of THEME_COLORS) {
    if (family.shades.includes(hex)) return family.shades
  }
  return null
}

/** Build the resolved cover URL from current state. */
function resolvedCoverUrl() {
  if (customCoverImageUrl.value) return customCoverImageUrl.value
  if (coverImage.value) return encodeURI(`/static/cover_gallery/${coverImage.value}`)
  return ''
}

/** Measure cover brightness and update coverDark flag. */
async function detectCoverBrightness() {
  const url = resolvedCoverUrl()
  if (!url) { coverDark.value = false; return }
  const brightness = await measureBrightness(url)
  coverDark.value = brightness < 100 // dark image threshold
}

const THEME_VARS = [
  '--theme-color', '--theme-rgb', '--theme-btn-text',
  '--theme-surface', '--theme-surface-hover', '--theme-border',
  '--theme-accent', '--theme-dark',
  '--theme-surface-rgb', '--theme-border-rgb', '--theme-accent-rgb', '--theme-dark-rgb',
]

const SEMANTIC_VARS = [
  '--color-primary', '--color-primary-strong', '--color-primary-soft',
  '--color-text-brand', '--color-focus-ring',
]

export function usePlatformCustomTheme() {
  const authStore = usePlatformAuthStore()

  function hydrate() {
    if (initialized) return
    const user = authStore.user
    if (user) {
      themeColor.value = user.theme_color || ''
      coverImage.value = user.cover_image || ''
      customCoverImageUrl.value = user.custom_cover_image || ''
    }
    applyTheme()
    detectCoverBrightness()
    initialized = true
  }

  function applyTheme() {
    /* c8 ignore next */
    if (typeof document === 'undefined') return
    const root = document.documentElement

    if (themeColor.value && themeColor.value.length === 7) {
      const { r, g, b } = hexToRgb(themeColor.value)
      const isLight = luminance(themeColor.value) > 186
      const shades = findColorFamily(themeColor.value)

      // Primary color
      root.style.setProperty('--theme-color', themeColor.value)
      root.style.setProperty('--theme-rgb', `${r}, ${g}, ${b}`)
      root.style.setProperty('--theme-btn-text', isLight ? '#1a1a1a' : '#ffffff')

      // Bridge to the semantic design-system tokens — overrides the values from
      // assets/styles/theme.css so base components (BaseButton, BaseBadge, etc.)
      // automatically pick up the tenant's brand color.
      root.style.setProperty('--color-primary', themeColor.value)
      root.style.setProperty('--color-primary-strong', shades ? shades[5] : themeColor.value)
      root.style.setProperty('--color-primary-soft', shades ? shades[0] : `rgba(${r}, ${g}, ${b}, 0.10)`)
      root.style.setProperty('--color-text-brand', shades ? shades[5] : themeColor.value)
      root.style.setProperty('--color-focus-ring', themeColor.value)

      if (shades) {
        // Full semantic palette from the shade family
        // shades[0]=lightest … shades[8]=darkest
        root.style.setProperty('--theme-surface', shades[0])
        root.style.setProperty('--theme-surface-hover', shades[1])
        root.style.setProperty('--theme-border', shades[2])
        root.style.setProperty('--theme-accent', shades[4])
        root.style.setProperty('--theme-dark', shades[5])
        // RGB versions for alpha usage in CSS
        root.style.setProperty('--theme-surface-rgb', toRgbString(shades[0]))
        root.style.setProperty('--theme-border-rgb', toRgbString(shades[2]))
        root.style.setProperty('--theme-accent-rgb', toRgbString(shades[4]))
        root.style.setProperty('--theme-dark-rgb', toRgbString(shades[5]))
      } else {
        // Fallback for any custom hex not in the palette
        root.style.setProperty('--theme-surface', `rgba(${r}, ${g}, ${b}, 0.07)`)
        root.style.setProperty('--theme-surface-hover', `rgba(${r}, ${g}, ${b}, 0.12)`)
        root.style.setProperty('--theme-border', `rgba(${r}, ${g}, ${b}, 0.20)`)
        root.style.setProperty('--theme-accent', `rgba(${r}, ${g}, ${b}, 0.45)`)
        root.style.setProperty('--theme-dark', themeColor.value)
        root.style.setProperty('--theme-surface-rgb', `${r}, ${g}, ${b}`)
        root.style.setProperty('--theme-border-rgb', `${r}, ${g}, ${b}`)
        root.style.setProperty('--theme-accent-rgb', `${r}, ${g}, ${b}`)
        root.style.setProperty('--theme-dark-rgb', `${r}, ${g}, ${b}`)
      }
    } else {
      THEME_VARS.forEach(v => root.style.removeProperty(v))
      // Reset semantic-token overrides so theme.css defaults take over again.
      SEMANTIC_VARS.forEach(v => root.style.removeProperty(v))
    }
  }

  async function setThemeColor(color) {
    themeColor.value = color
    applyTheme()
    try { await authStore.updateProfile({ theme_color: color }) } catch { /* silent */ }
  }

  async function setCoverImage(path) {
    coverImage.value = path
    customCoverImageUrl.value = ''
    applyTheme()
    detectCoverBrightness()
    try { await authStore.updateProfile({ cover_image: path }) } catch { /* silent */ }
  }

  async function setCustomCoverImage(file) {
    try {
      const formData = new FormData()
      formData.append('custom_cover_image', file)
      formData.append('cover_image', '')
      const { request } = usePlatformApi()
      const response = await request({
        url: 'me/',
        method: 'PATCH',
        data: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      if (response.data) {
        authStore.user = response.data
        customCoverImageUrl.value = response.data.custom_cover_image || ''
        coverImage.value = ''
        applyTheme()
        detectCoverBrightness()
      }
    } catch { /* silent */ }
  }

  async function clearCover() {
    coverImage.value = ''
    customCoverImageUrl.value = ''
    coverDark.value = false
    try { await authStore.updateProfile({ cover_image: '' }) } catch { /* silent */ }
  }

  async function clearAll() {
    themeColor.value = ''
    coverImage.value = ''
    customCoverImageUrl.value = ''
    coverDark.value = false
    applyTheme()
    try { await authStore.updateProfile({ theme_color: '', cover_image: '' }) } catch { /* silent */ }
  }

  const hasTheme = computed(() => Boolean(themeColor.value))
  const hasCover = computed(() => Boolean(coverImage.value) || Boolean(customCoverImageUrl.value))
  const isCoverDark = computed(() => coverDark.value)
  const isCustomized = computed(() => hasTheme.value || hasCover.value)

  return {
    THEME_COLORS,
    themeColor,
    coverImage,
    customCoverImageUrl,
    hasTheme,
    hasCover,
    isCoverDark,
    isCustomized,
    hydrate,
    applyTheme,
    setThemeColor,
    setCoverImage,
    setCustomCoverImage,
    clearCover,
    clearAll,
  }
}
