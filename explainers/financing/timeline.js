/* Construye el DOM de cada escena desde el contenido congelado + el guion y
   registra la única timeline GSAP (pausada) que HyperFrames recorre frame a frame. */
(function buildFinancingTimeline() {
  const {
    CONTENT, SCRIPT, el, icon, scene, timing, fill,
    caption, captionSequence, reveal, fade, sceneIntro, sceneOutro, register,
  } = window.EXPLAINER

  const hero = CONTENT.hero || {}
  const locale = CONTENT.locale || {}
  const eligibility = CONTENT.eligibility || {}
  const pkg = CONTENT.package || {}
  const conditions = CONTENT.conditions || []
  const options = CONTENT.options || []
  const values = {
    eyebrow: hero.eyebrow,
    title: hero.title,
    subtitle: hero.subtitle,
    trustNote: hero.trust_note,
    months: CONTENT.financingMonths,
    interest: CONTENT.ordinaryInterestRate,
    hours: pkg.hours,
    eligibilityBadge: eligibility.badge,
    eligibilityTitle: eligibility.title,
    ctaButton: (CONTENT.cta || {}).button,
    optionsTitle: locale.optionsTitle,
    optionsIntro: locale.optionsIntro,
  }
  const script = (id) => SCRIPT.scenes?.[id] || {}
  const text = (template, extra) => fill(template, extra ? { ...values, ...extra } : values)

  function wordmark() {
    return el('p', 'wordmark', 'Project App.')
  }
  function heading(sceneEl, copy, opts) {
    const options = opts || {}
    if (copy.eyebrow) sceneEl.appendChild(el('p', 'eyebrow', text(copy.eyebrow)))
    if (copy.title) sceneEl.appendChild(el(options.tag || 'h2', `title ${options.titleClass || 'title--md'}`, text(copy.title)))
    if (copy.lead) sceneEl.appendChild(el('p', 'lead', text(copy.lead)))
    if (copy.pill) sceneEl.appendChild(el('p', 'pill', text(copy.pill)))
  }

  const tl = gsap.timeline({ paused: true })

  /* ── Escena 1: marca + título del hero ────────────────────────────────── */
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

  /* ── Escena 3: cinco condiciones ──────────────────────────────────────── */
  const conds = scene('scene-conditions')
  conds.appendChild(wordmark())
  heading(conds, script('scene-conditions'))
  const condGrid = el('div', `cards cards--${Math.min(conditions.length, 5)}`)
  const condCopy = script('scene-conditions').conditions || {}
  conditions.forEach((condition, index) => {
    const card = el('article', 'card card--condition')
    const top = el('div', 'card__top')
    top.appendChild(el('span', 'card__index', condition.number || String(index + 1).padStart(2, '0')))
    top.appendChild(el('span', 'card__icon', icon(condition.icon)))
    card.appendChild(top)
    card.appendChild(el('h3', 'card__title', condition.title))
    condGrid.appendChild(card)
  })
  conds.appendChild(condGrid)
  {
    const { start, duration } = timing(conds)
    const at = sceneIntro(tl, conds, { captionDelay: 0.6 })
    const cards = condGrid.querySelectorAll('.card')
    const slot = (duration - (at - start) - 0.6) / Math.max(conditions.length, 1)
    const captions = []
    conditions.forEach((condition, index) => {
      const cardAt = at + index * slot
      reveal(tl, cards[index], cardAt, { y: 50, duration: 0.7, scale: 0.94 })
      const summary = condCopy[condition.id]
      if (summary) {
        captions.push({
          text: text(summary),
          at: cardAt + 0.1,
          until: index < conditions.length - 1 ? cardAt + slot : undefined,
        })
      }
    })
    captionSequence(tl, conds, captions)
  }
  sceneOutro(tl, conds)

  /* ── Escena 4: dos opciones ───────────────────────────────────────────── */
  const opts = scene('scene-options')
  opts.appendChild(wordmark())
  heading(opts, script('scene-options'))
  const optGrid = el('div', 'cards cards--2')
  const factsCopy = script('scene-options').facts || {}
  options.forEach((option) => {
    const card = el('article', `card option ${option.recommended ? 'card--accent' : ''}`.trim())
    card.appendChild(el('span', `option__badge ${option.recommended ? 'option__badge--recommended' : 'option__badge--alternative'}`, option.badge))
    card.appendChild(el('h3', 'option__name', option.name))
    const facts = el('ul', 'option__facts')
    const extra = { years: option.exclusivity_years, cycles: option.financing_cycles }
    ;(factsCopy[option.id] || []).forEach((fact) => facts.appendChild(el('li', null, text(fact, extra))))
    card.appendChild(facts)
    optGrid.appendChild(card)
  })
  opts.appendChild(optGrid)
  caption(opts, text(script('scene-options').caption))
  {
    const at = sceneIntro(tl, opts)
    reveal(tl, optGrid.querySelectorAll('.card'), at, { y: 60, duration: 0.9, stagger: 0.35, scale: 0.95 })
    reveal(tl, optGrid.querySelectorAll('.option__facts li'), at + 0.9, { y: 18, duration: 0.5, stagger: 0.18 })
  }
  sceneOutro(tl, opts)

  /* ── Escena 5: cómo aplicar ───────────────────────────────────────────── */
  const apply = scene('scene-apply')
  apply.appendChild(wordmark())
  heading(apply, script('scene-apply'))
  const beatsWrap = el('div', 'beats')
  const beats = script('scene-apply').beats || []
  beats.forEach((beat, index) => {
    const item = el('div', 'beat')
    item.appendChild(el('span', 'beat__index', String(index + 1)))
    item.appendChild(el('span', 'beat__text', text(beat)))
    beatsWrap.appendChild(item)
  })
  apply.appendChild(beatsWrap)
  caption(apply, text(script('scene-apply').caption))
  {
    const at = sceneIntro(tl, apply)
    reveal(tl, beatsWrap.querySelectorAll('.beat'), at, { y: 40, duration: 0.7, stagger: 1.4 })
  }
  sceneOutro(tl, apply)

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
