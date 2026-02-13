import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

function splitToSpans(element, mode) {
  if (!element) return null

  const original = element.textContent ?? ''
  const fragments = []

  element.textContent = ''

  const tokens =
    mode === 'words'
      ? (original.match(/\S+|\s+/g) ?? [])
      : Array.from(original)

  for (const token of tokens) {
    const span = document.createElement('span')
    span.style.display = 'inline-block'

    if (mode === 'chars') {
      span.textContent = token === ' ' ? '\u00A0' : token
    } else {
      span.textContent = token
    }

    element.appendChild(span)
    fragments.push(span)
  }

  const revert = () => {
    element.textContent = original
  }

  return { original, fragments, revert }
}

function normalizeScrollTrigger(st, element) {
  if (!st) return undefined
  return {
    trigger: element,
    start: 'top 85%',
    toggleActions: 'play none none reverse',
    ...st
  }
}

export function alphaReveal(element, options = {}) {
  const { duration = 0.8, delay = 0, ease = 'power3.out', scrollTrigger } = options
  if (!element) return null

  gsap.set(element, { opacity: 0 })
  return gsap.to(element, {
    opacity: 1,
    duration,
    delay,
    ease,
    scrollTrigger: normalizeScrollTrigger(scrollTrigger, element)
  })
}

export function characterSplitReveal(element, options = {}) {
  const {
    duration = 0.9,
    delay = 0,
    stagger = 0.02,
    y = 16,
    ease = 'power3.out',
    scrollTrigger
  } = options

  const split = splitToSpans(element, 'chars')
  if (!split) return null

  gsap.set(split.fragments, { y, opacity: 0 })

  const tween = gsap.to(split.fragments, {
    y: 0,
    opacity: 1,
    duration,
    delay,
    ease,
    stagger,
    scrollTrigger: normalizeScrollTrigger(scrollTrigger, element),
    onComplete: () => {
      split.revert()
    }
  })

  return tween
}

export function wordSplitReveal(element, options = {}) {
  const {
    duration = 0.9,
    delay = 0,
    stagger = 0.06,
    y = 18,
    ease = 'power3.out',
    scrollTrigger
  } = options

  const split = splitToSpans(element, 'words')
  if (!split) return null

  gsap.set(split.fragments, { y, opacity: 0 })

  const tween = gsap.to(split.fragments, {
    y: 0,
    opacity: 1,
    duration,
    delay,
    ease,
    stagger,
    scrollTrigger: normalizeScrollTrigger(scrollTrigger, element),
    onComplete: () => {
      split.revert()
    }
  })

  return tween
}

export function slideCharReveal(element, options = {}) {
  const {
    duration = 0.9,
    delay = 0,
    stagger = 0.02,
    x = 14,
    ease = 'power3.out',
    scrollTrigger
  } = options

  const split = splitToSpans(element, 'chars')
  if (!split) return null

  gsap.set(split.fragments, { x, opacity: 0 })

  const tween = gsap.to(split.fragments, {
    x: 0,
    opacity: 1,
    duration,
    delay,
    ease,
    stagger,
    scrollTrigger: normalizeScrollTrigger(scrollTrigger, element),
    onComplete: () => {
      split.revert()
    }
  })

  return tween
}

export function upDownReveal(element, options = {}) {
  const {
    duration = 0.9,
    delay = 0,
    y = 10,
    ease = 'power3.out',
    scrollTrigger
  } = options

  if (!element) return null

  gsap.set(element, { y: -y, opacity: 0 })
  return gsap.to(element, {
    y: 0,
    opacity: 1,
    duration,
    delay,
    ease,
    scrollTrigger: normalizeScrollTrigger(scrollTrigger, element)
  })
}

export function scrambleTextReveal(element, options = {}) {
  const {
    duration = 1.2,
    delay = 0,
    ease = 'none',
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    scrollTrigger
  } = options

  if (!element) return null

  const original = element.textContent ?? ''
  const state = { p: 0 }

  const update = () => {
    const length = original.length
    const revealCount = Math.floor(state.p * length)
    let out = ''

    for (let i = 0; i < length; i += 1) {
      if (i < revealCount) {
        out += original[i]
        continue
      }
      const c = chars[Math.floor(Math.random() * chars.length)]
      out += original[i] === ' ' ? ' ' : c
    }

    element.textContent = out
  }

  const tween = gsap.to(state, {
    p: 1,
    duration,
    delay,
    ease,
    onUpdate: update,
    onComplete: () => {
      element.textContent = original
    },
    scrollTrigger: normalizeScrollTrigger(scrollTrigger, element)
  })

  update()
  return tween
}
