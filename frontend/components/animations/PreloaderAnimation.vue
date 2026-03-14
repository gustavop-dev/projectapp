<template>
  <div>
    <!-- Preloader animation inspired by Quechua -->
    <div ref="preloaderContainer" v-show="isLoading" class="fixed inset-0 z-[999] bg-white flex flex-col items-center justify-center overflow-hidden">
      <!-- Scattered images like thrown photographs -->
      <div class="relative w-full h-full flex items-center justify-center">
        <!-- Central cube image -->
        <div ref="centralCube" class="absolute rounded-xl bg-white overflow-hidden shadow-lg border-4 border-white transform scale-0 z-10 flex items-center justify-center">
          <img ref="centralImage" src="~/assets/images/preloadingAnimation/Logo-White-ProjectApp.png" alt="Project App central cube" class="max-w-full max-h-full object-contain" @load="handleImageLoad" />
        </div>
        
        <!-- Image 1 -->
        <div ref="photoContainer1" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white flex items-center justify-center" style="transform: scale(0); rotate: -12deg; z-index: 1;">
          <img ref="photo1" src="~/assets/images/preloadingAnimation/1.jpg" alt="Project App showcase 1" class="max-w-full max-h-full object-contain" @load="handleImageLoad" />
          <div ref="photoText1" class="absolute bottom-4 left-4 flex items-center opacity-0">
            <span :class="[fontState.text1, sizeState.text1, 'text-white transform -rotate-3']">{{ globalMessages.photo_text1 }}</span>
            <img 
              ref="photoArrow1" 
              :src="arrowState.arrow1 ? simplyArrow1 : simplyArrow2" 
              alt="Arrow" 
              class="ml-2 w-12 h-8 transform translate-x-2 opacity-0" 
              @load="handleArrowLoad"
            />
          </div>
        </div>
        
        <!-- Image 2 -->
        <div ref="photoContainer2" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white flex items-center justify-center" style="transform: scale(0); rotate: 8deg; z-index: 2;">
          <img ref="photo2" src="~/assets/images/preloadingAnimation/2.jpg" alt="Project App showcase 2" class="max-w-full max-h-full object-contain" @load="handleImageLoad" />
          <div ref="photoText2" class="absolute top-4 right-4 flex items-center opacity-0">
            <span :class="[fontState.text2, sizeState.text2, 'text-white transform rotate-2']">{{ globalMessages.photo_text2 }}</span>
            <img 
              ref="photoArrow2" 
              :src="arrowState.arrow2 ? loopArrow1 : loopArrow2" 
              alt="Arrow" 
              class="ml-2 w-12 h-8 transform translate-x-2 opacity-0" 
              @load="handleArrowLoad"
            />
          </div>
        </div>

        <!-- Image 3 -->
        <div ref="photoContainer3" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white flex items-center justify-center" style="transform: scale(0); rotate: -6deg; z-index: 3;">
          <img ref="photo3" src="~/assets/images/preloadingAnimation/3.jpg" alt="Project App showcase 3" class="max-w-full max-h-full object-contain" @load="handleImageLoad" />
          <div ref="photoText3" class="absolute bottom-4 right-4 flex items-center opacity-0">
            <span :class="[fontState.text3, sizeState.text3, 'text-white transform -rotate-1']">{{ globalMessages.photo_text3 }}</span>
            <img 
              ref="photoArrow3" 
              :src="arrowState.arrow3 ? simplyArrow1 : simplyArrow2" 
              alt="Arrow" 
              class="ml-2 w-12 h-8 transform translate-x-2 opacity-0" 
              @load="handleArrowLoad"
            />
          </div>
        </div>

        <!-- Image 4 -->
        <div ref="photoContainer4" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white flex items-center justify-center" style="transform: scale(0); rotate: 9deg; z-index: 4;">
          <img ref="photo4" src="~/assets/images/preloadingAnimation/4.jpg" alt="Project App showcase 4" class="max-w-full max-h-full object-contain" @load="handleImageLoad" />
          <div ref="photoText4" class="absolute top-4 left-4 flex items-center opacity-0">
            <span :class="[fontState.text4, sizeState.text4, 'text-white transform rotate-1']">{{ globalMessages.photo_text4 }}</span>
            <img 
              ref="photoArrow4" 
              :src="arrowState.arrow4 ? loopArrow1 : loopArrow2" 
              alt="Arrow" 
              class="ml-2 w-12 h-8 transform translate-x-2 opacity-0" 
              @load="handleArrowLoad"
            />
          </div>
        </div>

        <!-- Image 5 - The one that fades at the end -->
        <div ref="photoContainer5" class="absolute rounded-xl overflow-hidden shadow-lg border-4 border-white flex items-center justify-center" style="transform: scale(0); rotate: -5deg; z-index: 5;">
          <img ref="photo5" src="~/assets/images/preloadingAnimation/5.jpeg" alt="Project App showcase 5" class="max-w-full max-h-full object-contain" @load="handleImageLoad" />
          <div ref="photoText5" class="absolute bottom-4 left-4 flex items-center opacity-0">
            <span :class="[fontState.text5, sizeState.text5, 'text-white transform -rotate-2']">{{ globalMessages.photo_text5 }}</span>
            <img 
              ref="photoArrow5" 
              :src="arrowState.arrow5 ? simplyArrow1 : simplyArrow2" 
              alt="Arrow" 
              class="ml-2 w-12 h-8 transform translate-x-2 opacity-0" 
              @load="handleArrowLoad"
            />
          </div>
        </div>
      </div>
      
      <!-- Collection texts with animated arrows - initially hidden with v-show -->
      <div ref="collectionContainer" v-show="imagesLoaded" 
           class="absolute flex items-center opacity-0"
           :class="[
             isDesktop ? 'left-44 bottom-52' : 'left-8 bottom-36'
           ]">
        <span :class="[
          fontState.mainText1, 
          isDesktop ? sizeState.mainText1 : 'text-[22px]', 
          'text-black transform -rotate-12 whitespace-pre-line'
        ]">{{ globalMessages.left_text }}</span>
        <img 
          ref="simplyArrowMain" 
          :src="mainArrowState.simply ? simplyArrow1 : simplyArrow2" 
          alt="Simply Arrow" 
          :class="[
            'ml-4 rotate-180',
            isDesktop ? 'w-32 h-24' : 'w-20 h-16'
          ]"
          @load="handleArrowLoad"
        />
      </div>
      
      <div ref="spiritContainer" v-show="imagesLoaded" 
           class="absolute flex items-center opacity-0"
           :class="[
             isDesktop ? 'right-80 top-72' : 'right-8 top-32'
           ]">
        <img 
          ref="loopArrowMain" 
          :src="mainArrowState.loop ? loopArrow1 : loopArrow2" 
          alt="Loop Arrow" 
          :class="[
            'ml-4 -rotate-45 scale-y-[-1] mr-4',
            isDesktop ? 'w-32 h-24' : 'w-20 h-16'
          ]"
          @load="handleArrowLoad"
        />
        <span :class="[
          fontState.mainText2, 
          isDesktop ? sizeState.mainText2 : 'text-[22px]', 
          'text-black pb-12 transform rotate-12 whitespace-pre-line ml-2'
        ]">{{ globalMessages.right_text }}</span>
      </div>
      
      <!-- Only the percentage centered on screen -->
      <div class="absolute bottom-10 left-0 right-0 flex justify-center">
        <div :class="[isDesktop ? 'text-2xl' : 'text-lg', 'text-esmerald font-light']">
          <span ref="progressText">0%</span>
        </div>
      </div>

      <!-- F9: Personalized greeting overlay -->
      <div
        v-if="clientName"
        ref="personalizedOverlay"
        class="absolute inset-0 z-20 flex items-center justify-center bg-white opacity-0 pointer-events-none"
      >
        <p class="text-2xl sm:text-3xl md:text-4xl font-light text-esmerald text-center px-8 leading-relaxed">
          <span class="block text-base sm:text-lg text-esmerald/50 mb-2 font-light tracking-wider">{{ personalizedSubtext }}</span>
          <span class="font-medium text-esmerald">{{ clientName }}</span>
        </p>
      </div>
    </div>

    <!-- White overlay for transition animation - Removed when completely finished -->
    <div v-if="isOverlayVisible" ref="whiteOverlay" class="fixed inset-0 z-[99] bg-white transform origin-center scale-0 rotate-0"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, reactive } from 'vue'
import { gsap } from 'gsap'
import { useGlobalMessages } from '~/composables/useMessages'

// Import arrow images
import simplyArrow1 from '../../assets/images/arrows/simply_arrow_1.png'
import simplyArrow2 from '../../assets/images/arrows/simply_arrow_2.png'
import loopArrow1 from '../../assets/images/arrows/loop_arrow_1.png'
import loopArrow2 from '../../assets/images/arrows/loop_arrow_2.png'

// Use global messages for the preloader section
const { globalMessages } = useGlobalMessages('preloader')

// Props to allow control from parent component
const props = defineProps({
  // Whether to show the animation
  active: {
    type: Boolean,
    default: true
  },
  // CSS class for elements that should be animated when revealed
  revealClass: {
    type: String,
    default: '.animate-on-reveal'
  },
  // Client name for personalized greeting
  clientName: {
    type: String,
    default: ''
  },
  // Language for personalized text
  language: {
    type: String,
    default: 'es'
  }
})

const personalizedSubtext = computed(() => {
  return props.language === 'en' ? 'Prepared especially for' : 'Preparado especialmente para'
})

const personalizedOverlay = ref(null)

// Events emitted to parent component
const emit = defineEmits(['animationComplete'])

// Local state for loading and visibility control
const isLoading = ref(props.active)
const isOverlayVisible = ref(props.active) // New ref to control the overlay
const preloaderContainer = ref(null) // New ref for the main container

// Image loading control
const totalImages = 11 // 5 photos + 4 arrows + central cube + 1 extra margin
const loadedImages = ref(0)
const imagesLoaded = ref(false)

// Function to handle image loading
const handleImageLoad = () => {
  loadedImages.value++
  checkImagesLoaded()
}

// Function to handle arrow loading
const handleArrowLoad = () => {
  loadedImages.value++
  checkImagesLoaded()
}

// Check if all images are loaded
const checkImagesLoaded = () => {
  if (loadedImages.value >= totalImages) {
    imagesLoaded.value = true
    // Start animation only when images are loaded
    if (props.active && !animationStarted.value) {
      setTimeout(() => {
        animatePreloader()
      }, 100)
    }
  }
}

// Animation start control
const animationStarted = ref(false)

// State for toggling between the two arrow variants
const arrowState = reactive({
  arrow1: true,
  arrow2: true,
  arrow3: true,
  arrow4: true,
  arrow5: true
})

// State for main arrows
const mainArrowState = reactive({
  simply: true,
  loop: true
})

// State for toggling between different Caveat fonts
const fontState = reactive({
  text1: 'font-caveat-regular',
  text2: 'font-caveat-medium',
  text3: 'font-caveat-semibold',
  text4: 'font-caveat-bold',
  text5: 'font-caveat-regular',
  mainText1: 'font-caveat-semibold',
  mainText2: 'font-caveat-bold'
})

// State for toggling text sizes
const sizeState = reactive({
  text1: 'text-[16.25px]',
  text2: 'text-[16px]',
  text3: 'text-[16.25px]',
  text4: 'text-[16px]',
  text5: 'text-[16.25px]',
  mainText1: 'text-[28px]',
  mainText2: 'text-[28px]'
})

// Array of fonts to rotate
const fontClasses = ['font-caveat-regular', 'font-caveat-medium', 'font-caveat-semibold', 'font-caveat-bold']

// Array of sizes to alternate - subtle micro variations
const textSizes = ['text-[16px]', 'text-[16.25px]']
const mainTextSizes = ['text-[28px]', 'text-[28.5px]']

// References for main arrows and texts
const collectionContainer = ref(null)
const spiritContainer = ref(null)
const simplyArrowMain = ref(null)
const loopArrowMain = ref(null)

// References for animation elements - 5 photos
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
const centralCube = ref(null)

const progressText = ref(null)
const whiteOverlay = ref(null)

// Watch for changes in the active prop
const isDesktop = ref(window.innerWidth >= 1024)

// Redefine positions when screen size changes
const updatePositions = () => {
  isDesktop.value = window.innerWidth >= 1024;
  
  // If images are already loaded and visible, update positions
  if (imagesLoaded.value) {
    if (collectionContainer.value) {
      if (isDesktop.value) {
        // Desktop positions
        gsap.set(collectionContainer.value, { left: '11rem', bottom: '13rem' });
      } else {
        // Mobile positions - adjusted for better visibility
        gsap.set(collectionContainer.value, { left: '2rem', bottom: '7rem' });
      }
    }
    
    if (spiritContainer.value) {
      if (isDesktop.value) {
        gsap.set(spiritContainer.value, { right: '20rem', top: '18rem' });
      } else {
        gsap.set(spiritContainer.value, { right: '2rem', top: '3rem' });
      }
    }
  }
}

// Total estimated animation duration (in seconds)
const ANIMATION_DURATION = 2.0  // Reduced to 2 seconds maximum

// Function to animate arrows by switching their variants
const animateArrows = () => {
  // Animate the photo arrows
  const arrows = [
    { state: arrowState, key: 'arrow1' },
    { state: arrowState, key: 'arrow2' },
    { state: arrowState, key: 'arrow3' },
    { state: arrowState, key: 'arrow4' },
    { state: arrowState, key: 'arrow5' }
  ]
  
  // Animate the main arrows
  const mainArrows = [
    { state: mainArrowState, key: 'simply' },
    { state: mainArrowState, key: 'loop' }
  ]
  
  // Every 140ms change the state of the arrows (slightly slower for better visual effect)
  let arrowInterval = setInterval(() => {
    // Change the photo arrows
    arrows.forEach(arrow => {
      arrow.state[arrow.key] = !arrow.state[arrow.key]
    })
    
    // Change the main arrows
    mainArrows.forEach(arrow => {
      arrow.state[arrow.key] = !arrow.state[arrow.key]
    })
    
    // Change fonts and sizes
    animateFonts()
    
  }, 140)
  
  // The interval will now be cleared in the finishAnimation function
  // We don't set a timeout here so it continues until the end  
  
  return arrowInterval
}

// Function to animate fonts
const animateFonts = () => {
  // Get random indices for each text
  const textKeys = ['text1', 'text2', 'text3', 'text4', 'text5']
  
  // Update each text with a random font and size
  textKeys.forEach(key => {
    // Change font randomly among the 4 options
    const randomFontIndex = Math.floor(Math.random() * fontClasses.length)
    fontState[key] = fontClasses[randomFontIndex]
    
    // Toggle size
    sizeState[key] = sizeState[key] === textSizes[0] ? textSizes[1] : textSizes[0]
  })
  
  // Toggle main texts between medium and semibold
  fontState.mainText1 = fontState.mainText1 === 'font-caveat-semibold' ? 'font-caveat-bold' : 'font-caveat-semibold'
  fontState.mainText2 = fontState.mainText2 === 'font-caveat-bold' ? 'font-caveat-semibold' : 'font-caveat-bold'
  
  // Toggle main text sizes
  sizeState.mainText1 = sizeState.mainText1 === mainTextSizes[0] ? mainTextSizes[1] : mainTextSizes[0]
  sizeState.mainText2 = sizeState.mainText2 === mainTextSizes[0] ? mainTextSizes[1] : mainTextSizes[0]
}

// Function to set photo sizes and positions
const setPhotoSizes = () => {
  const baseSize = isDesktop.value ? 1 : 0.7 // Slightly reduced for mobile
  
  // All photo containers centered, varying slightly in position
  
  // Central cube (logo) - Size and position adjusted
  if (centralCube.value) {
    gsap.set(centralCube.value, {
      width: `${260 * baseSize}px`,
      height: `${175 * baseSize}px`,
      x: 0,
      y: isDesktop.value ? 0 : '-50px', // Move up on mobile devices
    });
  }
  
  // Photo 1 - Slightly down and left
  if (photoContainer1.value) {
    gsap.set(photoContainer1.value, { 
      width: `${300 * baseSize}px`, 
      height: `${200 * baseSize}px`,
      x: `${-20 * baseSize}px`, 
      y: `${15 * baseSize}px`,
    });
  }
  
  // Photo 2 - Slightly up and right
  if (photoContainer2.value) {
    gsap.set(photoContainer2.value, { 
      width: `${280 * baseSize}px`, 
      height: `${190 * baseSize}px`,
      x: `${30 * baseSize}px`, 
      y: `${-25 * baseSize}px`,
    });
  }
  
  // Photo 3 - Slightly down and left
  if (photoContainer3.value) {
    gsap.set(photoContainer3.value, { 
      width: `${310 * baseSize}px`, 
      height: `${210 * baseSize}px`,
      x: `${-25 * baseSize}px`, 
      y: `${-10 * baseSize}px`,
    });
  }
  
  // Photo 4 - Slightly up and right
  if (photoContainer4.value) {
    gsap.set(photoContainer4.value, { 
      width: `${290 * baseSize}px`, 
      height: `${195 * baseSize}px`,
      x: `${20 * baseSize}px`, 
      y: `${25 * baseSize}px`,
    });
  }
  
  // Photo 5 - Centered
  if (photoContainer5.value) {
    gsap.set(photoContainer5.value, { 
      width: `${320 * baseSize}px`, 
      height: `${215 * baseSize}px`,
      x: `${0}px`, 
      y: `${0}px`,
    });
  }
}

// Variable to store the arrow animation interval
let arrowInterval = null

// Helper function to safely animate elements with null checks
const safeAnimate = (timeline, target, properties, timing = undefined) => {
  if (target) {
    if (timing !== undefined) {
      return timeline.to(target, properties, timing);
    } else {
      return timeline.to(target, properties);
    }
  }
  return timeline;
};

// Function to animate the preloader with 5 photos
const animatePreloader = () => {
  // Mark that the animation has started
  animationStarted.value = true;
  
  const hasPersonalizedGreeting = !!(props.clientName && personalizedOverlay.value);
  const forceTimeout = hasPersonalizedGreeting ? 3500 : 2000;

  // Set a maximum timeout to ensure animation ends
  const forceFinishTimeout = setTimeout(() => {
    if (isLoading.value) {
      console.log('Forcing preloader to finish after timeout');
      finishAnimation();
    }
  }, forceTimeout);
  
  // Main timeline
  const mainTimeline = gsap.timeline({
    onComplete: () => {
      clearTimeout(forceFinishTimeout);
      if (hasPersonalizedGreeting) {
        showPersonalizedGreeting();
      } else {
        finishAnimation();
      }
    }
  });

  // Start the arrow animation
  arrowInterval = animateArrows()

  // Create a counter for the percentage that increases throughout the animation
  let progress = { value: 0 };
  
  // Animate the percentage during the duration
  mainTimeline.to(progress, {
    value: 100,
    duration: ANIMATION_DURATION,
    ease: "linear",
    onUpdate: () => {
      // Update the percentage text on each frame with null check
      if (progressText.value) {
        progressText.value.textContent = `${Math.round(progress.value)}%`;
      }
    }
  }, 0);
  
  // Animate the main texts with arrows (now at the beginning)
  if (collectionContainer.value) {
    mainTimeline.to(collectionContainer.value, {
      opacity: 1,
      x: 0,
      duration: 0.6,
      ease: 'back.out'
    }, 0.1);
  }
  
  if (spiritContainer.value) {
    mainTimeline.to(spiritContainer.value, {
      opacity: 1,
      x: 0,
      duration: 0.6,
      ease: 'back.out'
    }, 0.2);
  }
  
  // Photo 1 - Slower movement
  if (photoContainer1.value) {
    mainTimeline.to(photoContainer1.value, { 
      scale: 1, 
      duration: 0.45, // Increased duration
      ease: 'back.out(1.3)', // Smoother easing
      rotation: -12
    }, 0.05);
  }
  
  if (photoText1.value) {
    mainTimeline.to(photoText1.value, { 
      opacity: 1, 
      duration: 0.3 // Increased duration
    }, "+=0.05");
  }
  
  if (photoArrow1.value) {
    mainTimeline.to(photoArrow1.value, { 
      opacity: 1, 
      x: 0, 
      duration: 0.2 // Increased duration
    }, "-=0.15");
  }
  
  // Photo 2 - Slower movement
  safeAnimate(mainTimeline, photoContainer2.value, { 
    scale: 1, 
    duration: 0.45, // Increased duration
    ease: 'back.out(1.3)', // Smoother easing
    rotation: 8
  }, 0.30); // Slightly delayed start
  
  safeAnimate(mainTimeline, photoText2.value, { 
    opacity: 1, 
    duration: 0.3 // Increased duration
  }, "+=0.05");
  
  safeAnimate(mainTimeline, photoArrow2.value, { 
    opacity: 1, 
    x: 0, 
    duration: 0.2 // Increased duration
  }, "-=0.15");
  
  // Photo 3 - Slower movement
  safeAnimate(mainTimeline, photoContainer3.value, { 
    scale: 1, 
    duration: 0.45, // Increased duration
    ease: 'back.out(1.3)', // Smoother easing
    rotation: -6
  }, 0.55); // Slightly delayed start
  
  safeAnimate(mainTimeline, photoText3.value, { 
    opacity: 1, 
    duration: 0.3 // Increased duration
  }, "+=0.05");
  
  safeAnimate(mainTimeline, photoArrow3.value, { 
    opacity: 1, 
    x: 0, 
    duration: 0.2 // Increased duration
  }, "-=0.15");
  
  // Photo 4 - Slower movement
  safeAnimate(mainTimeline, photoContainer4.value, { 
    scale: 1, 
    duration: 0.45, // Increased duration
    ease: 'back.out(1.3)', // Smoother easing
    rotation: 9
  }, 0.80); // Slightly delayed start
  
  safeAnimate(mainTimeline, photoText4.value, { 
    opacity: 1, 
    duration: 0.3 // Increased duration
  }, "+=0.05");
  
  safeAnimate(mainTimeline, photoArrow4.value, { 
    opacity: 1, 
    x: 0, 
    duration: 0.2 // Increased duration
  }, "-=0.15");
  
  // Photo 5 - The last one that fades away - Slower movement
  safeAnimate(mainTimeline, photoContainer5.value, { 
    scale: 1, 
    duration: 0.45, // Increased duration
    ease: 'back.out(1.3)', // Smoother easing
    rotation: -5
  }, 1.05); // Slightly delayed start
  
  safeAnimate(mainTimeline, photoText5.value, { 
    opacity: 1, 
    duration: 0.3 // Increased duration
  }, "+=0.05");
  
  safeAnimate(mainTimeline, photoArrow5.value, { 
    opacity: 1, 
    x: 0, 
    duration: 0.2 // Increased duration
  }, "-=0.15");
  
  // Animate the central cube - after the photos
  safeAnimate(mainTimeline, centralCube.value, {
    scale: 1,
    rotation: 0,
    duration: 0.5, // Increased duration
    ease: 'back.out(1.2)',
  }, 1.40); // Timing adjusted to fit within total duration
  
  // Start the continuous floating animation
  startFloatingAnimation();
}

// Function to start the continuous floating animation
const floatingTl = ref(null);
const startFloatingAnimation = () => {
  // If an animation already exists, stop and remove it
  if (floatingTl.value) {
    floatingTl.value.kill();
  }
  
  // Create a new timeline for the floating animation
  floatingTl.value = gsap.timeline({
    repeat: -1, // Repeat indefinitely
    yoyo: true  // Go back and forth for a more natural effect
  });
  
  // Animate all photo containers with a smooth floating effect
  const photoContainers = [photoContainer1.value, photoContainer2.value, photoContainer3.value, 
                          photoContainer4.value, photoContainer5.value].filter(el => el !== null);
  
  if (photoContainers.length > 0) {
    floatingTl.value.to(photoContainers, {
      y: '-=4',       // Move 4px up
      duration: 1.2,  // For 1.2 seconds
      ease: 'sine.inOut',
      stagger: {
        each: 0.15,   // Offset between elements
        from: "random" // Start from a random element for more naturalness
      }
    }).to(photoContainers, {
      y: '+=4',       // Move back 4px down
      duration: 1.2,  // For 1.2 seconds
      ease: 'sine.inOut',
      stagger: {
        each: 0.15,   // Offset between elements
        from: "random" // Start from a random element for more naturalness
      }
    });
  }
  
  // Also slightly animate the central cube
  if (centralCube.value) {
    floatingTl.value.to(centralCube.value, {
      y: '-=2',       // Move only 2px for a more subtle effect
      duration: 1.5,  // Slightly slower
      ease: 'sine.inOut',
    }, 0).to(centralCube.value, {
      y: '+=2',       // Move back 2px down
      duration: 1.5,  // Slightly slower
      ease: 'sine.inOut',
    }, 1.5);
  }
}

// F9: Show personalized greeting overlay for 1.5s before finishing
const showPersonalizedGreeting = () => {
  if (!personalizedOverlay.value) {
    finishAnimation();
    return;
  }

  // Stop arrow animation during greeting
  if (arrowInterval) {
    clearInterval(arrowInterval);
    arrowInterval = null;
  }

  const greetingTl = gsap.timeline({
    onComplete: () => {
      finishAnimation();
    }
  });

  // Fade in the personalized overlay over existing content
  greetingTl.to(personalizedOverlay.value, {
    opacity: 1,
    duration: 0.4,
    ease: 'power2.out'
  });

  // Hold for 1.5s then fade out
  greetingTl.to(personalizedOverlay.value, {
    opacity: 0,
    duration: 0.3,
    ease: 'power2.in',
    delay: 1.5
  });
}

// Separate function to handle the end of the animation
const finishAnimation = () => {
  // Check if animation already finished to prevent duplicate calls
  if (!isLoading.value) return;
  
  // Timeline for the exit animation, must complete in 0.5 seconds
  const finishTl = gsap.timeline({
    onComplete: () => {
      // Clean up the arrow animation interval AFTER completing the animation
      if (arrowInterval) {
        clearInterval(arrowInterval)
        arrowInterval = null
      }
      
      // Stop and remove the floating animation
      if (floatingTl.value) {
        floatingTl.value.kill();
        floatingTl.value = null;
      }
      
      // Set isLoading to false after the fade-out animation
      isLoading.value = false
      
      // Remove the overlay completely immediately
      isOverlayVisible.value = false
      
      // Notify the parent component
      emit('animationComplete')
      
      // Check if elements with the reveal class exist before animating
      const elementsToAnimate = document.querySelectorAll(props.revealClass);
      if (elementsToAnimate.length > 0) {
        // Set initial state
        elementsToAnimate.forEach(el => {
          el.style.opacity = "0";
          el.style.transform = "translateY(30px)";
        });
        
        // Animate them
        gsap.to(elementsToAnimate, {
          y: 0,
          opacity: 1,
          stagger: 0.05,
          duration: 0.3,
          ease: 'power2.out'
        });
      }
    }
  });
  
  // Parallel timeline for fading out the container with fade-out
  if (preloaderContainer.value) {
    gsap.to(preloaderContainer.value, {
      opacity: 0,
      duration: 0.3,
      ease: 'power2.inOut'
    });
  }
  
  // First animate the exit of the main texts
  const mainTexts = [collectionContainer.value, spiritContainer.value].filter(el => el !== null);
  if (mainTexts.length > 0) {
    gsap.to(mainTexts, {
      opacity: 0,
      duration: 0.18, // Adjusted duration
      ease: 'power2.in'
    });
  }
  
  // Animate the exit of the photos and overlay in parallel and quickly
  // Central cube animation with null check
  if (centralCube.value) {
    finishTl.to(centralCube.value, {
      scale: 1.4,
      opacity: 0,
      duration: 0.22, // Adjusted duration
      ease: 'power2.in'
    }, 0);
  }
  
  // Photo 5 animation with null check
  if (photoContainer5.value) {
    finishTl.to(photoContainer5.value, {
      scale: 1.2,
      opacity: 0,
      duration: 0.18, // Adjusted duration
      ease: 'power2.in'
    }, 0.03); // Adjusted timing
  }
  
  // Photos 1-4 animation with null check
  const photoContainers = [photoContainer1.value, photoContainer2.value, photoContainer3.value, photoContainer4.value].filter(el => el !== null);
  if (photoContainers.length > 0) {
    finishTl.to(photoContainers, {
      scale: 0.8,
      opacity: 0,
      stagger: 0.02,
      duration: 0.15, // Maintained duration
      ease: 'power2.in'
    }, 0.06); // Adjusted timing
  }
  
  // White overlay animation with null check
  if (whiteOverlay.value) {
    finishTl.to(whiteOverlay.value, {
      scale: 12,
      rotate: 360,
      duration: 0.25, // Adjusted duration
      ease: 'power3.inOut'
    }, 0.1); // Adjusted timing
  }
}

// Debounced resize handler
let resizeTimeout
function handleResize() {
  clearTimeout(resizeTimeout)
  resizeTimeout = setTimeout(() => {
    updatePositions(); // Actualizar posiciones cuando cambia el tamaño de la pantalla
    setPhotoSizes(); // Update sizes when screen size changes
  }, 150)
}

// Start animation when component mounts
onMounted(() => {
  // Ensure initial opacity
  if (preloaderContainer.value) {
    preloaderContainer.value.style.opacity = '1';
  }
  
  // Set initial photo sizes
  setPhotoSizes()
  
  // Set initial positions
  updatePositions();
  
  // Safety fallback: force animation start if images haven't loaded after 4s
  setTimeout(() => {
    if (!animationStarted.value && props.active) {
      imagesLoaded.value = true
      animatePreloader()
    }
  }, 4000)
  
  // Add resize event
  window.addEventListener('resize', handleResize, { passive: true })
  
  // Clean up event listener when unmounting
  return () => {
    window.removeEventListener('resize', handleResize)
    clearTimeout(resizeTimeout)
    
    // Clean up the arrow animation interval if it exists
    if (arrowInterval) {
      clearInterval(arrowInterval)
    }
  }
})

// Watch for changes in the active prop
watch(() => props.active, (newValue) => {
  if (newValue) {
    // If activated, ensure full opacity before showing
    if (preloaderContainer.value) {
      preloaderContainer.value.style.opacity = '1';
    }
    isLoading.value = true;
    isOverlayVisible.value = true;
    
    if (photoContainer1.value) {
      // If activated and elements are already mounted, restart the animation
      animatePreloader()
    }
  }
}, { immediate: true })
</script>