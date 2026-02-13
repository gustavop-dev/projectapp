import { onMounted, onBeforeUnmount, ref, getCurrentInstance } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { TextPlugin } from 'gsap/TextPlugin'
import { SplitText } from 'gsap/SplitText'

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger, TextPlugin)

// Note: SplitText is a premium plugin, using alternative approach for free version

/**
 * Composable for text animations using GSAP
 * Provides reusable text animation functions with scroll triggers
 */
export function useTextAnimations() {
  const animatedElements = ref([])
  const scrollTriggers = ref([])

  /**
   * Fade In from Bottom animation
   * Text slides up and fades in on scroll
   */
  const fadeInFromBottom = (element, options = {}) => {
    const {
      delay = 0,
      duration = 0.8,
      distance = 50,
      ease = "power2.out",
      triggerStart = "top 80%",
      triggerEnd = "bottom 20%"
    } = options

    gsap.set(element, {
      y: distance * 0.5,
      opacity: 0.8
    })

    const animation = gsap.to(element, {
      y: 0,
      opacity: 1,
      duration,
      delay,
      ease,
      scrollTrigger: {
        trigger: element,
        start: triggerStart,
        end: triggerEnd,
        toggleActions: "play none none reverse",
        // markers: true, // Remove in production
      }
    })

    scrollTriggers.value.push(animation.scrollTrigger)
    animatedElements.value.push(element)
    return animation
  }

  /**
   * Fade In from Left animation
   * Text slides from left and fades in on scroll
   */
  const fadeInFromLeft = (element, options = {}) => {
    const {
      delay = 0,
      duration = 0.8,
      distance = 80,
      ease = "power2.out",
      triggerStart = "top 80%"
    } = options

    gsap.set(element, {
      x: -distance * 0.3,
      opacity: 0.8
    })

    const animation = gsap.to(element, {
      x: 0,
      opacity: 1,
      duration,
      delay,
      ease,
      scrollTrigger: {
        trigger: element,
        start: triggerStart,
        toggleActions: "play none none reverse"
      }
    })

    scrollTriggers.value.push(animation.scrollTrigger)
    animatedElements.value.push(element)
    return animation
  }

  /**
   * Fade In from Right animation
   * Text slides from right and fades in on scroll
   */
  const fadeInFromRight = (element, options = {}) => {
    const {
      delay = 0,
      duration = 0.8,
      distance = 80,
      ease = "power2.out",
      triggerStart = "top 80%"
    } = options

    gsap.set(element, {
      x: distance * 0.3,
      opacity: 0.8
    })

    const animation = gsap.to(element, {
      x: 0,
      opacity: 1,
      duration,
      delay,
      ease,
      scrollTrigger: {
        trigger: element,
        start: triggerStart,
        toggleActions: "play none none reverse"
      }
    })

    scrollTriggers.value.push(animation.scrollTrigger)
    animatedElements.value.push(element)
    return animation
  }

  /**
   * Scale In animation
   * Text scales from small to normal size on scroll
   */
  const scaleIn = (element, options = {}) => {
    const {
      delay = 0,
      duration = 0.6,
      scale = 0.8,
      ease = "back.out(1.7)",
      triggerStart = "top 80%"
    } = options

    gsap.set(element, {
      scale: 0.95,
      opacity: 0.9
    })

    const animation = gsap.to(element, {
      scale: 1,
      opacity: 1,
      duration,
      delay,
      ease,
      scrollTrigger: {
        trigger: element,
        start: triggerStart,
        toggleActions: "play none none reverse"
      }
    })

    scrollTriggers.value.push(animation.scrollTrigger)
    animatedElements.value.push(element)
    return animation
  }

  /**
   * Typewriter Effect animation
   * Text appears character by character
   */
  const typewriter = (element, options = {}) => {
    const {
      delay = 0,
      duration = 2,
      triggerStart = "top 80%"
    } = options

    const originalText = element.textContent
    
    gsap.set(element, {
      opacity: 1
    })

    const animation = gsap.fromTo(element, 
      {
        text: ""
      },
      {
        text: originalText,
        duration,
        delay,
        ease: "none",
        scrollTrigger: {
          trigger: element,
          start: triggerStart,
          toggleActions: "play none none reverse"
        }
      }
    )

    scrollTriggers.value.push(animation.scrollTrigger)
    animatedElements.value.push(element)
    return animation
  }

  /**
   * Stagger animation for multiple elements
   * Animates a group of elements with staggered timing
   */
  const staggerFadeIn = (elements, options = {}) => {
    const {
      delay = 0,
      duration = 0.6,
      stagger = 0.1,
      distance = 30,
      ease = "power2.out",
      triggerStart = "top 80%",
      from = "bottom"
    } = options

    const initialProps = from === "bottom" 
      ? { y: distance * 0.3, opacity: 0.8 }
      : from === "left"
      ? { x: -distance * 0.3, opacity: 0.8 }
      : from === "right"
      ? { x: distance * 0.3, opacity: 0.8 }
      : { scale: 0.95, opacity: 0.9 }

    const finalProps = from === "bottom" 
      ? { y: 0, opacity: 1 }
      : from === "left" || from === "right"
      ? { x: 0, opacity: 1 }
      : { scale: 1, opacity: 1 }

    gsap.set(elements, initialProps)

    const animation = gsap.to(elements, {
      ...finalProps,
      duration,
      delay,
      ease,
      stagger,
      scrollTrigger: {
        trigger: elements[0],
        start: triggerStart,
        toggleActions: "play none none reverse"
      }
    })

    scrollTriggers.value.push(animation.scrollTrigger)
    elements.forEach(el => animatedElements.value.push(el))
    return animation
  }

  /**
   * Word reveal animation
   * Reveals text word by word with mask effect
   */
  const wordReveal = (element, options = {}) => {
    const {
      delay = 0,
      duration = 1.2,
      stagger = 0.1,
      ease = "power2.out",
      triggerStart = "top 80%"
    } = options

    // Split text into words manually (free alternative to SplitText)
    const text = element.textContent
    const words = text.split(' ')
    
    // Clear original content
    element.innerHTML = ''
    
    // Create span for each word
    const wordElements = words.map(word => {
      const span = document.createElement('span')
      span.textContent = word + ' '
      span.style.display = 'inline-block'
      span.style.overflow = 'hidden'
      element.appendChild(span)
      return span
    })

    // Set initial state
    gsap.set(wordElements, {
      y: '100%',
      opacity: 0
    })

    const animation = gsap.to(wordElements, {
      y: '0%',
      opacity: 1,
      duration,
      delay,
      ease,
      stagger,
      scrollTrigger: {
        trigger: element,
        start: triggerStart,
        toggleActions: "play none none reverse"
      }
    })

    scrollTriggers.value.push(animation.scrollTrigger)
    animatedElements.value.push(element)
    return animation
  }

  /**
   * Counter animation
   * Animates numbers from 0 to target value
   */
  const counterAnimation = (element, options = {}) => {
    const {
      delay = 0,
      duration = 2,
      targetValue = 100,
      suffix = '',
      prefix = '',
      ease = "power2.out",
      triggerStart = "top 80%"
    } = options

    const counter = { value: 0 }

    const animation = gsap.to(counter, {
      value: targetValue,
      duration,
      delay,
      ease,
      onUpdate: () => {
        element.textContent = prefix + Math.round(counter.value) + suffix
      },
      scrollTrigger: {
        trigger: element,
        start: triggerStart,
        toggleActions: "play none none reverse"
      }
    })

    scrollTriggers.value.push(animation.scrollTrigger)
    animatedElements.value.push(element)
    return animation
  }

  /**
   * Timeline for complex animations
   * Creates a GSAP timeline for orchestrating multiple animations
   */
  const createTimeline = (options = {}) => {
    const {
      triggerElement,
      triggerStart = "top 80%",
      delay = 0
    } = options

    const tl = gsap.timeline({
      delay,
      scrollTrigger: {
        trigger: triggerElement,
        start: triggerStart,
        toggleActions: "play none none reverse"
      }
    })

    if (tl.scrollTrigger) {
      scrollTriggers.value.push(tl.scrollTrigger)
    }

    return tl
  }

  /**
   * Cleanup function to remove all animations and scroll triggers
   */
  const cleanup = () => {
    // Kill all scroll triggers
    scrollTriggers.value.forEach(trigger => {
      if (trigger) trigger.kill()
    })
    
    // Clear all animations
    animatedElements.value.forEach(element => {
      gsap.killTweensOf(element)
    })
    
    // Clear arrays
    scrollTriggers.value = []
    animatedElements.value = []
    
    // Refresh ScrollTrigger
    ScrollTrigger.refresh()
  }

  /**
   * Refresh ScrollTrigger (useful for dynamic content)
   */
  const refreshScrollTrigger = () => {
    ScrollTrigger.refresh()
  }

  // Only register lifecycle hooks if called during component setup
  if (getCurrentInstance()) {
    // Cleanup on component unmount
    onBeforeUnmount(() => {
      cleanup()
    })

    // Setup ScrollTrigger on mount
    onMounted(() => {
      ScrollTrigger.refresh()
    })
  }

  return {
    // Animation functions
    fadeInFromBottom,
    fadeInFromLeft,
    fadeInFromRight,
    scaleIn,
    typewriter,
    staggerFadeIn,
    wordReveal,
    counterAnimation,
    createTimeline,
    
    // Utility functions
    cleanup,
    refreshScrollTrigger,
    
    // Reactive data
    animatedElements,
    scrollTriggers
  }
}

/**
 * Preset animations for common use cases
 */
export const textAnimationPresets = {
  // Section titles
  sectionTitle: {
    duration: 1,
    distance: 60,
    ease: "power3.out",
    triggerStart: "top 85%"
  },
  
  // Subtitles
  subtitle: {
    duration: 0.8,
    distance: 40,
    ease: "power2.out",
    delay: 0.2,
    triggerStart: "top 85%"
  },
  
  // Paragraphs
  paragraph: {
    duration: 0.6,
    distance: 30,
    ease: "power2.out",
    delay: 0.4,
    triggerStart: "top 85%"
  },
  
  // Cards/Items
  card: {
    duration: 0.5,
    distance: 40,
    ease: "back.out(1.7)",
    triggerStart: "top 85%"
  },
  
  // Statistics/Numbers
  statistic: {
    duration: 1.5,
    scale: 0.5,
    ease: "elastic.out(1, 0.5)",
    triggerStart: "top 85%"
  },
  
  // Buttons
  button: {
    duration: 0.4,
    scale: 0.9,
    ease: "back.out(1.7)",
    delay: 0.6,
    triggerStart: "top 85%"
  }
}
