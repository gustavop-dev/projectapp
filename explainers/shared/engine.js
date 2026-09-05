/* Helpers compartidos por las composiciones. Se carga después de gsap.min.js,
   content.js y script.js; expone window.EXPLAINER. Todo es síncrono: la
   timeline debe quedar registrada antes de que HyperFrames empiece a buscar frames. */
window.EXPLAINER = (function buildExplainerHelpers() {
  const CONTENT = window.EXPLAINER_CONTENT || {}
  const SCRIPT = window.EXPLAINER_SCRIPT || {}
  const iconOverrides = SCRIPT.iconOverrides || {}
  const EASE_IN = 'power3.out'
  const EASE_OUT = 'power2.in'

  function el(tag, className, text, attrs) {
    const node = document.createElement(tag)
    if (className) node.className = className
    if (text !== undefined && text !== null) node.textContent = text
    if (attrs) Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value))
    return node
  }

  function icon(glyph) {
    return iconOverrides[glyph] || glyph || '＋'
  }

  function scene(id) {
    const node = document.getElementById(id)
    if (!node) throw new Error(`Falta la escena #${id} en index.html`)
    return node
  }

  function timing(sceneEl) {
    return {
      start: Number(sceneEl.dataset.start),
      duration: Number(sceneEl.dataset.duration),
      end: Number(sceneEl.dataset.start) + Number(sceneEl.dataset.duration),
    }
  }

  function fill(template, values) {
    return String(template || '').replace(/\{(\w+)\}/g, (match, key) => (values[key] ?? match))
  }

  function listJoin(items, conjunction) {
    if (items.length <= 1) return items.join('')
    return `${items.slice(0, -1).join(', ')} ${conjunction} ${items[items.length - 1]}`
  }

  function caption(sceneEl, text) {
    if (!text) return null
    const node = el('p', 'caption', text)
    sceneEl.appendChild(node)
    return node
  }

  function reveal(tl, targets, at, opts) {
    const options = opts || {}
    const y = options.y === undefined ? 40 : options.y
    const duration = options.duration === undefined ? 0.8 : options.duration
    const stagger = options.stagger === undefined ? 0.12 : options.stagger
    const from = { opacity: 0, y }
    const to = { opacity: 1, y: 0, duration, ease: EASE_IN, stagger }
    if (options.scale !== undefined) {
      from.scale = options.scale
      to.scale = 1
    }
    tl.fromTo(targets, from, to, at)
    return tl
  }

  function fade(tl, targets, at, opts) {
    const options = opts || {}
    const duration = options.duration === undefined ? 0.5 : options.duration
    tl.to(targets, { opacity: 0, duration, ease: EASE_OUT }, at)
    return tl
  }

  /* Entrada estándar de una escena: logo, eyebrow, título, lead y pill en cascada. */
  function sceneIntro(tl, sceneEl, opts) {
    const options = opts || {}
    const { start } = timing(sceneEl)
    let at = start + (options.delay === undefined ? 0.15 : options.delay)
    const selectors = ['.logo--hero', '.eyebrow', '.title', '.lead', '.pill']
    selectors.forEach((selector) => {
      const nodes = sceneEl.querySelectorAll(selector)
      if (!nodes.length) return
      reveal(tl, nodes, at, { y: 36, duration: 0.9 })
      at += 0.35
    })
    const cap = sceneEl.querySelector('.caption')
    if (cap) reveal(tl, cap, start + (options.captionDelay === undefined ? 0.7 : options.captionDelay), { y: 24, duration: 0.6 })
    return at
  }

  /* Salida estándar: todo el contenido de la escena se desvanece antes del corte. */
  function sceneOutro(tl, sceneEl, opts) {
    const options = opts || {}
    const lead = options.lead === undefined ? 0.5 : options.lead
    const { end } = timing(sceneEl)
    fade(tl, sceneEl.querySelectorAll(':scope > *'), end - lead, { duration: lead })
    return tl
  }

  /* Varios subtítulos en una escena, uno por beat: [{ text, at, until }]. */
  function captionSequence(tl, sceneEl, items) {
    items.forEach((item) => {
      const node = caption(sceneEl, item.text)
      if (!node) return
      reveal(tl, node, item.at, { y: 24, duration: 0.5 })
      if (item.until !== undefined) fade(tl, node, item.until - 0.35, { duration: 0.35 })
    })
  }

  /* Deja la timeline lista; index.html la registra en window.__timelines["main"]
     con un script inline para que el lint estático de HyperFrames la detecte. */
  function register(tl) {
    window.EXPLAINER_TIMELINE = tl
    return tl
  }

  return {
    CONTENT,
    SCRIPT,
    el,
    icon,
    scene,
    timing,
    fill,
    listJoin,
    caption,
    captionSequence,
    reveal,
    fade,
    sceneIntro,
    sceneOutro,
    register,
  }
})()
