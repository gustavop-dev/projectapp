import { onUnmounted, ref, watch } from 'vue'

export function useFreeResources({ videos = [], images = [], modals = [] } = {}) {
  // Referencia para manejar el estado de los modales
  const modalRefs = modals.map(() => ref(false))

  // Función para liberar videos e imágenes
  const freeMediaResources = () => {
    videos.forEach(video => {
      if (video.value) {
        video.value.src = '' // Liberar recurso de video
        video.value.load()   // Forzar recarga de un video vacío
      }
    })
    images.forEach(image => {
      if (image.value) {
        image.value.src = '' // Liberar recurso de imagen
      }
    })
  }

  // Función para desmontar modales
  const closeModals = () => {
    modalRefs.forEach(modalRef => {
      modalRef.value = false
    })
  }

  // Vigila los modales y los cierra cuando el componente se desmonta
  watch(modalRefs, (newValues) => {
    if (newValues.some(isOpen => isOpen)) {
      closeModals()
    }
  })

  onUnmounted(() => {
    freeMediaResources()
    closeModals()
  })

  return {
    modalRefs,
    closeModals,
    freeMediaResources
  }
}
