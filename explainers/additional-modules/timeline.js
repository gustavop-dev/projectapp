/* Construye el DOM de cada escena desde el contenido congelado + el guion y
   registra la única timeline GSAP (pausada) que HyperFrames recorre frame a frame. */
(function buildAdditionalModulesTimeline() {
  const {
    CONTENT, SCRIPT, el, icon, scene, timing, fill, listJoin,
    caption, captionSequence, reveal, fade, sceneIntro, sceneOutro, register,
  } = window.EXPLAINER

  const NUMBER_WORDS = ['cero', 'una', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez']
  const locale = CONTENT.locale || {}
  const categories = CONTENT.categories || []
  const modules = categories.flatMap((category, index) => category.modules.map((module) => ({ ...module, tone: (index % 5) + 1 })))
  const lowerNames = categories.map((category) => category.name.toLowerCase())
  const lastName = lowerNames[lowerNames.length - 1] || ''
  const values = {
    eyebrow: locale.eyebrow,
    title: locale.title,
    subtitle: locale.subtitle,
    noPriceNotice: locale.noPriceNotice,
    total: CONTENT.totalModules,
    categoryCount: NUMBER_WORDS[categories.length] || String(categories.length),
    categories: listJoin(lowerNames, /^(i|hi)/.test(lastName) ? 'e' : 'y'),
  }
  const script = (id) => SCRIPT.scenes?.[id] || {}
  const text = (template) => fill(template, values)

  function wordmark() {
    return el('p', 'wordmark', 'Project App.')
  }
  function heading(sceneEl, copy, options) {
    const opts = options || {}
    if (copy.eyebrow) sceneEl.appendChild(el('p', 'eyebrow', text(copy.eyebrow)))
    if (copy.title) sceneEl.appendChild(el(opts.tag || 'h2', `title ${opts.titleClass || 'title--md'}`, text(copy.title)))
    if (copy.lead) sceneEl.appendChild(el('p', 'lead', text(copy.lead)))
    if (copy.pill) sceneEl.appendChild(el('p', 'pill', text(copy.pill)))
  }

  const tl = gsap.timeline({ paused: true })

  /* ── Escena 1: marca + título ─────────────────────────────────────────── */
  const intro = scene('scene-intro')
  intro.appendChild(wordmark())
  heading(intro, script('scene-intro'), { tag: 'h1', titleClass: '' })
  caption(intro, text(script('scene-intro').caption))
  sceneIntro(tl, intro)
  sceneOutro(tl, intro)

  /* ── Escena 2: qué es ─────────────────────────────────────────────────── */
  const what = scene('scene-what')
  what.appendChild(wordmark())
  heading(what, script('scene-what'))
  caption(what, text(script('scene-what').caption))
  sceneIntro(tl, what)
  sceneOutro(tl, what)

  /* ── Escena 3: cinco categorías ───────────────────────────────────────── */
  const cats = scene('scene-categories')
  cats.appendChild(wordmark())
  heading(cats, script('scene-categories'))
  const catGrid = el('div', `cards cards--${Math.min(categories.length, 5)}`)
  categories.forEach((category, index) => {
    const card = el('article', 'card', null, { 'data-tone': String((index % 5) + 1) })
    const top = el('div', 'card__top')
    const icons = el('div', 'card__icons')
    category.modules.slice(0, 3).forEach((module) => icons.appendChild(el('span', 'chip__icon', icon(module.icon))))
    top.appendChild(icons)
    top.appendChild(el('span', 'card__count', String(category.count)))
    card.appendChild(top)
    card.appendChild(el('h3', 'card__title', category.name))
    catGrid.appendChild(card)
  })
  cats.appendChild(catGrid)
  caption(cats, text(script('scene-categories').caption))
  {
    const at = sceneIntro(tl, cats)
    reveal(tl, catGrid.querySelectorAll('.card'), at, { y: 60, duration: 0.9, stagger: 0.28, scale: 0.94 })
  }
  sceneOutro(tl, cats)

  /* ── Escena 4: carrusel de módulos ────────────────────────────────────── */
  const carousel = scene('scene-carousel')
  carousel.appendChild(wordmark())
  heading(carousel, script('scene-carousel'))
  const rowsWrap = el('div', 'carousel', null, { 'data-layout-allow-overflow': '' })
  const rowCount = 3
  const perRow = Math.ceil(modules.length / rowCount)
  const rows = []
  for (let rowIndex = 0; rowIndex < rowCount; rowIndex += 1) {
    const row = el('div', 'carousel__row', null, { 'data-layout-allow-overflow': '' })
    modules.slice(rowIndex * perRow, (rowIndex + 1) * perRow).forEach((module) => {
      const chip = el('span', 'chip', null, { 'data-tone': String(module.tone) })
      chip.appendChild(el('span', 'chip__icon', icon(module.icon)))
      chip.appendChild(el('span', 'chip__label', module.name))
      row.appendChild(chip)
    })
    rowsWrap.appendChild(row)
    rows.push(row)
  }
  carousel.appendChild(rowsWrap)
  caption(carousel, text(script('scene-carousel').caption))
  {
    const { start, duration } = timing(carousel)
    const at = sceneIntro(tl, carousel)
    reveal(tl, rows, at, { y: 30, duration: 0.8, stagger: 0.2 })
    rows.forEach((row, index) => {
      // El desplazamiento se calcula en el primer render (fuentes ya cargadas):
      // cada fila recorre su ancho completo dentro de la escena.
      tl.to(row, {
        x: () => -Math.max(0, row.scrollWidth - 1640 + (index * 120)),
        duration: duration - 3.2,
        ease: 'none',
        immediateRender: false,
      }, start + 1.6)
    })
  }
  sceneOutro(tl, carousel)

  /* ── Escena 5: cómo explorarlo (3 beats) ──────────────────────────────── */
  const how = scene('scene-how')
  how.appendChild(wordmark())
  heading(how, script('scene-how'))
  const beatsWrap = el('div', 'beats')
  const beats = script('scene-how').beats || []
  beats.forEach((beat, index) => {
    const item = el('div', 'beat')
    item.appendChild(el('span', 'beat__index', String(index + 1)))
    item.appendChild(el('span', 'beat__text', text(beat.text)))
    beatsWrap.appendChild(item)
  })
  how.appendChild(beatsWrap)
  {
    const { start, duration } = timing(how)
    const at = sceneIntro(tl, how, { captionDelay: 0.6 })
    const slot = (duration - (at - start) - 0.6) / Math.max(beats.length, 1)
    const items = beatsWrap.querySelectorAll('.beat')
    const captions = []
    beats.forEach((beat, index) => {
      const beatAt = at + index * slot
      reveal(tl, items[index], beatAt, { y: 40, duration: 0.7 })
      captions.push({ text: text(beat.caption), at: beatAt + 0.1, until: index < beats.length - 1 ? beatAt + slot : undefined })
    })
    captionSequence(tl, how, captions)
  }
  sceneOutro(tl, how)

  /* ── Escena 6: cierre ─────────────────────────────────────────────────── */
  const close = scene('scene-close')
  close.appendChild(wordmark())
  heading(close, script('scene-close'), { tag: 'h2', titleClass: 'title--md' })
  caption(close, text(script('scene-close').caption))
  sceneIntro(tl, close)
  {
    const { end } = timing(close)
    fade(tl, close.querySelectorAll(':scope > *'), end - 0.9, { duration: 0.9 })
  }

  register(tl)
})()
