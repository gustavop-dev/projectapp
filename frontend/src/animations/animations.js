import gsap from 'gsap'

export function fadeUp(element, options = {}) {
  const {
    y = 24,
    opacity = 0,
    duration = 0.8,
    delay = 0,
    ease = 'power3.out',
    scrollTrigger
  } = options

  if (!element) return null

  const vars = {
    y: 0,
    opacity: 1,
    duration,
    delay,
    ease
  }

  if (scrollTrigger) {
    vars.scrollTrigger = {
      trigger: element,
      start: 'top 85%',
      toggleActions: 'play none none reverse',
      ...scrollTrigger
    }
  }

  gsap.set(element, { y, opacity })
  return gsap.to(element, vars)
}

export function staggerFadeUp(elements, options = {}) {
  const {
    y = 20,
    opacity = 0,
    duration = 0.6,
    delay = 0,
    stagger = 0.12,
    ease = 'power3.out',
    scrollTrigger
  } = options

  if (!elements || elements.length === 0) return null

  const vars = {
    y: 0,
    opacity: 1,
    duration,
    delay,
    stagger,
    ease
  }

  if (scrollTrigger) {
    vars.scrollTrigger = {
      trigger: elements[0],
      start: 'top 85%',
      toggleActions: 'play none none reverse',
      ...scrollTrigger
    }
  }

  gsap.set(elements, { y, opacity })
  return gsap.to(elements, vars)
}

export function waveEmoji(element, options = {}) {
  const {
    rotation = 20,
    duration = 0.3,
    repeat = 5,
    delay = 0.5,
    ease = 'power1.inOut',
    transformOrigin = 'bottom center'
  } = options

  if (!element) return null

  return gsap.to(element, {
    rotation,
    transformOrigin,
    duration,
    ease,
    yoyo: true,
    repeat,
    delay
  })
}
