<template>
  <div>
    <!-- Preloader animation inspired by Quechua -->
    <div ref="preloaderContainer" v-show="isLoading" class="fixed inset-0 z-[999] bg-white flex flex-col items-center justify-center overflow-hidden">
      <!-- Imágenes dispersas como fotografías tiradas -->
      <div class="relative w-full h-full flex items-center justify-center">
        <!-- Imagen 1 -->
        <div ref="photoContainer1" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white" style="transform: scale(0); rotate: -12deg; z-index: 1;">
          <img src="@/assets/images/home/cube_illusion.webp" alt="Project App showcase 1" class="w-full h-full object-cover" />
          <div ref="photoText1" class="absolute bottom-4 left-4 flex items-center opacity-0">
            <span class="text-white text-sm font-light">NUESTRO ENFOQUE 2025</span>
            <svg ref="photoArrow1" class="ml-2 w-5 h-5 text-white transform translate-x-2 opacity-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path>
            </svg>
          </div>
        </div>
        
        <!-- Imagen 2 -->
        <div ref="photoContainer2" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white" style="transform: scale(0); rotate: 8deg; z-index: 2;">
          <img src="@/assets/images/home/cube_illusion.webp" alt="Project App showcase 2" class="w-full h-full object-cover" />
          <div ref="photoText2" class="absolute top-4 right-4 flex items-center opacity-0">
            <span class="text-white text-sm font-light">ESPÍRITU DIGITAL</span>
            <svg ref="photoArrow2" class="ml-2 w-5 h-5 text-white transform translate-x-2 opacity-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path>
            </svg>
          </div>
        </div>

        <!-- Imagen 3 -->
        <div ref="photoContainer3" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white" style="transform: scale(0); rotate: -6deg; z-index: 3;">
          <img src="@/assets/images/home/cube_illusion.webp" alt="Project App showcase 3" class="w-full h-full object-cover" />
          <div ref="photoText3" class="absolute bottom-4 right-4 flex items-center opacity-0">
            <span class="text-white text-sm font-light">EXPERIENCIA VISUAL</span>
            <svg ref="photoArrow3" class="ml-2 w-5 h-5 text-white transform translate-x-2 opacity-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path>
            </svg>
          </div>
        </div>

        <!-- Imagen 4 -->
        <div ref="photoContainer4" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white" style="transform: scale(0); rotate: 9deg; z-index: 4;">
          <img src="@/assets/images/home/cube_illusion.webp" alt="Project App showcase 4" class="w-full h-full object-cover" />
          <div ref="photoText4" class="absolute top-4 left-4 flex items-center opacity-0">
            <span class="text-white text-sm font-light">DISEÑO CREATIVO</span>
            <svg ref="photoArrow4" class="ml-2 w-5 h-5 text-white transform translate-x-2 opacity-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path>
            </svg>
          </div>
        </div>

        <!-- Imagen 5 - La que se desvanece al final -->
        <div ref="photoContainer5" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white" style="transform: scale(0); rotate: -5deg; z-index: 5;">
          <img src="@/assets/images/home/cube_illusion.webp" alt="Project App showcase 5" class="w-full h-full object-cover" />
          <div ref="photoText5" class="absolute bottom-4 left-4 flex items-center opacity-0">
            <span class="text-white text-sm font-light">INNOVACIÓN 2025</span>
            <svg ref="photoArrow5" class="ml-2 w-5 h-5 text-white transform translate-x-2 opacity-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path>
            </svg>
          </div>
        </div>
      </div>
      
      <!-- Solo el porcentaje centrado en la pantalla -->
      <div class="absolute bottom-10 left-0 right-0 flex justify-center">
        <div class="text-esmerald text-2xl font-light">
          <span ref="progressText">0%</span>
        </div>
      </div>
    </div>

    <!-- White overlay for transition animation - Removido cuando termina completamente -->
    <div v-if="isOverlayVisible" ref="whiteOverlay" class="fixed inset-0 z-[99] bg-white transform origin-center scale-0 rotate-0"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { gsap } from 'gsap'

// Props para permitir control desde el componente padre
const props = defineProps({
  // Si se debe mostrar la animación
  active: {
    type: Boolean,
    default: true
  },
  // Clase CSS para elementos que se deben animar al revelar
  revealClass: {
    type: String,
    default: '.animate-on-reveal'
  }
})

// Eventos emitidos al componente padre
const emit = defineEmits(['animationComplete'])

// Estado local para control de carga y visibilidad
const isLoading = ref(props.active)
const isOverlayVisible = ref(props.active) // Nueva ref para controlar el overlay
const preloaderContainer = ref(null) // Nueva ref para el contenedor principal

// Referencias para los elementos de la animación - 5 fotos
const photoContainer1 = ref(null)
const photoText1 = ref(null)
const photoArrow1 = ref(null)
const photoContainer2 = ref(null)
const photoText2 = ref(null)
const photoArrow2 = ref(null)
const photoContainer3 = ref(null)
const photoText3 = ref(null)
const photoArrow3 = ref(null)
const photoContainer4 = ref(null)
const photoText4 = ref(null)
const photoArrow4 = ref(null)
const photoContainer5 = ref(null)
const photoText5 = ref(null)
const photoArrow5 = ref(null)

const progressText = ref(null)
const whiteOverlay = ref(null)

// Observar cambios en el prop active
const isDesktop = ref(window.innerWidth >= 1024)

// Duración total estimada de la animación (en segundos)
const ANIMATION_DURATION = 2.0  // Reducida para permitir tiempo para el desvanecimiento

// Función para configurar los tamaños y posiciones de las fotos
const setPhotoSizes = () => {
  const baseSize = isDesktop.value ? 1 : 0.75 // Factor de escala para móvil
  
  // Todos los contenedores de fotos centrados, solo varían ligeramente en posición
  
  // Foto 1 - Ligeramente hacia abajo izquierda
  gsap.set(photoContainer1.value, { 
    width: `${300 * baseSize}px`, 
    height: `${220 * baseSize}px`,
    x: `${-20 * baseSize}px`, 
    y: `${15 * baseSize}px`,
  })
  
  // Foto 2 - Ligeramente hacia arriba derecha
  gsap.set(photoContainer2.value, { 
    width: `${280 * baseSize}px`, 
    height: `${200 * baseSize}px`,
    x: `${30 * baseSize}px`, 
    y: `${-25 * baseSize}px`,
  })
  
  // Foto 3 - Ligeramente hacia abajo izquierda
  gsap.set(photoContainer3.value, { 
    width: `${310 * baseSize}px`, 
    height: `${230 * baseSize}px`,
    x: `${-25 * baseSize}px`, 
    y: `${-10 * baseSize}px`,
  })
  
  // Foto 4 - Ligeramente hacia arriba derecha
  gsap.set(photoContainer4.value, { 
    width: `${290 * baseSize}px`, 
    height: `${210 * baseSize}px`,
    x: `${20 * baseSize}px`, 
    y: `${25 * baseSize}px`,
  })
  
  // Foto 5 - Centrada
  gsap.set(photoContainer5.value, { 
    width: `${320 * baseSize}px`, 
    height: `${235 * baseSize}px`,
    x: `${0}px`, 
    y: `${0}px`,
  })
}

// Función para animar la preloader con 5 fotos
const animatePreloader = () => {
  // Línea de tiempo principal
  const mainTimeline = gsap.timeline({
    onComplete: () => {
      // Cuando se complete la línea de tiempo principal, ejecutar la animación de finalización inmediatamente
      finishAnimation();
    }
  });

  // Creamos un contador para el porcentaje que se incrementa durante toda la animación
  let progress = { value: 0 };
  
  // Animación del porcentaje durante la duración
  mainTimeline.to(progress, {
    value: 100,
    duration: ANIMATION_DURATION,
    ease: "linear",
    onUpdate: () => {
      // Actualizar el texto del porcentaje en cada frame
      progressText.value.textContent = `${Math.round(progress.value)}%`;
    }
  }, 0);
  
  // Foto 1
  mainTimeline.to(photoContainer1.value, { 
    scale: 1, 
    duration: 0.35,
    ease: 'back.out(1.5)',
    rotation: -12
  }, 0.05);
  
  mainTimeline.to(photoText1.value, { 
    opacity: 1, 
    duration: 0.2 
  }, "+=0.05");
  
  mainTimeline.to(photoArrow1.value, { 
    opacity: 1, 
    x: 0, 
    duration: 0.15
  }, "-=0.1");
  
  // Foto 2
  mainTimeline.to(photoContainer2.value, { 
    scale: 1, 
    duration: 0.35,
    ease: 'back.out(1.5)',
    rotation: 8
  }, 0.25);
  
  mainTimeline.to(photoText2.value, { 
    opacity: 1, 
    duration: 0.2 
  }, "+=0.05");
  
  mainTimeline.to(photoArrow2.value, { 
    opacity: 1, 
    x: 0, 
    duration: 0.15
  }, "-=0.1");
  
  // Foto 3
  mainTimeline.to(photoContainer3.value, { 
    scale: 1, 
    duration: 0.35,
    ease: 'back.out(1.5)',
    rotation: -6
  }, 0.5);
  
  mainTimeline.to(photoText3.value, { 
    opacity: 1, 
    duration: 0.2 
  }, "+=0.05");
  
  mainTimeline.to(photoArrow3.value, { 
    opacity: 1, 
    x: 0, 
    duration: 0.15
  }, "-=0.1");
  
  // Foto 4
  mainTimeline.to(photoContainer4.value, { 
    scale: 1, 
    duration: 0.35,
    ease: 'back.out(1.5)',
    rotation: 9
  }, 0.75);
  
  mainTimeline.to(photoText4.value, { 
    opacity: 1, 
    duration: 0.2 
  }, "+=0.05");
  
  mainTimeline.to(photoArrow4.value, { 
    opacity: 1, 
    x: 0, 
    duration: 0.15
  }, "-=0.1");
  
  // Foto 5 - La última que luego se desvanece
  mainTimeline.to(photoContainer5.value, { 
    scale: 1, 
    duration: 0.35,
    ease: 'back.out(1.5)',
    rotation: -5
  }, 1.0);
  
  mainTimeline.to(photoText5.value, { 
    opacity: 1, 
    duration: 0.2 
  }, "+=0.05");
  
  mainTimeline.to(photoArrow5.value, { 
    opacity: 1, 
    x: 0, 
    duration: 0.15
  }, "-=0.1");
  
  // Añadir una muy breve animación flotante
  mainTimeline.to([photoContainer1.value, photoContainer2.value, photoContainer3.value, photoContainer4.value, photoContainer5.value], {
    y: -2,
    duration: 0.4,
    yoyo: true,
    ease: 'sine.inOut',
    stagger: 0.05
  }, 1.4);
}

// Función separada para manejar el final de la animación
const finishAnimation = () => {
  // Timeline para la animación de salida, debe completarse en 0.5 segundos
  const finishTl = gsap.timeline({
    onComplete: () => {
      // Establecer isLoading a false después de la animación de desvanecimiento
      isLoading.value = false
      
      // Remover el overlay completamente de inmediato
      isOverlayVisible.value = false
      
      // Notificar al componente padre
      emit('animationComplete')
      
      // Animar la aparición del contenido principal inmediatamente
      document.querySelectorAll(props.revealClass).forEach(el => {
        el.style.opacity = "0";
        el.style.transform = "translateY(30px)";
      });
      
      gsap.to(props.revealClass, {
        y: 0,
        opacity: 1,
        stagger: 0.05,
        duration: 0.3,
        ease: 'power2.out'
      });
    }
  });
  
  // Timeline paralelo para el desvanecimiento del contenedor con fade-out
  gsap.to(preloaderContainer.value, {
    opacity: 0,
    duration: 0.3,
    ease: 'power2.inOut'
  });
  
  // Animar la salida de las fotos y el overlay en paralelo y rápidamente
  finishTl
    .to(photoContainer5.value, {
      scale: 1.2,
      opacity: 0,
      duration: 0.2,
      ease: 'power2.in'
    }, 0)
    .to([photoContainer1.value, photoContainer2.value, photoContainer3.value, photoContainer4.value], {
      scale: 0.8,
      opacity: 0,
      stagger: 0.02,
      duration: 0.15,
      ease: 'power2.in'
    }, 0)
    .to(whiteOverlay.value, {
      scale: 12,
      rotate: 360,
      duration: 0.3,
      ease: 'power3.inOut'
    }, 0);
}

// Debounced resize handler
let resizeTimeout
function handleResize() {
  clearTimeout(resizeTimeout)
  resizeTimeout = setTimeout(() => {
    isDesktop.value = window.innerWidth >= 1024
    setPhotoSizes() // Actualizar tamaños al cambiar el tamaño de pantalla
  }, 150)
}

// Iniciar animación al montar el componente
onMounted(() => {
  // Asegurar opacidad inicial
  if (preloaderContainer.value) {
    preloaderContainer.value.style.opacity = '1';
  }
  
  // Configurar tamaños iniciales de fotos
  setPhotoSizes()
  
  // Iniciar animación del preloader
  if (props.active) {
    animatePreloader()
  }
  
  // Agregar evento resize
  window.addEventListener('resize', handleResize, { passive: true })
  
  // Limpiar event listener al desmontar
  return () => {
    window.removeEventListener('resize', handleResize)
    clearTimeout(resizeTimeout)
  }
})

// Observar cambios en el prop active
watch(() => props.active, (newValue) => {
  if (newValue) {
    // Si se activa, asegurar opacidad completa antes de mostrar
    if (preloaderContainer.value) {
      preloaderContainer.value.style.opacity = '1';
    }
    isLoading.value = true;
    isOverlayVisible.value = true;
    
    if (photoContainer1.value) {
      // Si se activa y los elementos ya están montados, reiniciar la animación
      animatePreloader()
    }
  }
}, { immediate: true })
</script> 