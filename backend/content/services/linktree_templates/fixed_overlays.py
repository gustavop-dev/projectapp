"""Measure Chrome layout boxes, including roots and generated pseudo-elements."""


def _measure(session, viewport):
    snapshot = session.send('DOMSnapshot.captureSnapshot', {
        'computedStyles': ['position', 'visibility'], 'includeDOMRects': True,
    })
    strings = snapshot['strings']
    document = snapshot['documents'][0]
    nodes, layout = document['nodes'], document['layout']
    pseudos = set(nodes.get('pseudoType', {}).get('index', []))
    issues, fixed = {}, False
    for index, node in enumerate(layout['nodeIndex']):
        style = [strings[value] for value in layout['styles'][index]]
        if style != ['fixed', 'visible']:
            continue
        fixed = True
        x, y, width, height = layout['bounds'][index]
        x -= document['scrollOffsetX']
        y -= document['scrollOffsetY']
        area = (max(0, min(viewport['width'], x + width) - max(0, x))
                * max(0, min(viewport['height'], y + height) - max(0, y)))
        if area <= viewport['width'] * viewport['height'] * 0.2:
            continue
        owner = nodes['parentIndex'][node] if node in pseudos else node
        attributes = [strings[value] for value in nodes['attributes'][owner]]
        attributes = dict(zip(attributes[::2], attributes[1::2]))
        issues[owner] = {
            'severity': 'error', 'code': 'fixed_overlay', 'file': 'template.html',
            'line': int(attributes.get('data-template-line', 1)),
            'node': attributes.get('data-template-node'),
            'message': 'Un elemento fijo cubre más del 20 % de la pantalla.',
        }
    return list(issues.values()), fixed


def fixed_overlay_issues(page):
    """Use rendered geometry both now and at animation keyframes/midpoints."""
    session = page.context.new_cdp_session(page)
    animations = None
    try:
        issues, fixed = _measure(session, page.viewport_size)
        if issues or not fixed:
            return issues
        animations = page.evaluate_handle('''() => document.getAnimations().map(animation => ({
            animation, time: animation.currentTime, state: animation.playState
        }))''')
        samples = animations.evaluate('''entries => entries.flatMap(({animation}, index) => {
            const timing = animation.effect.getTiming();
            if (!Number.isFinite(Number(timing.duration))) return [];
            const offsets = animation.effect.getKeyframes().map(frame => frame.computedOffset);
            const samples = [...offsets, ...offsets.slice(1).map((value, i) => (value + offsets[i]) / 2)];
            return samples.map(offset => ({index, time: Number(timing.delay) + Number(timing.duration) * Math.min(.99999, offset)}));
        })''')
        # Bound synchronous validation work; never silently skip unchecked motion.
        if len(samples) > 120:
            return [{'severity': 'error', 'code': 'complexity', 'file': 'template.css',
                     'line': 1, 'message': 'Reduce los fotogramas de animación para validar los elementos fijos.'}]
        animations.evaluate('entries => entries.forEach(({animation}) => animation.pause())')
        for sample in samples:
            animations.evaluate('''(entries, sample) => {
                entries.forEach(({animation, time}) => { animation.currentTime = time; });
                entries[sample.index].animation.currentTime = sample.time;
            }''', sample)
            measured, _ = _measure(session, page.viewport_size)
            if measured:
                return measured
        return []
    finally:
        if animations is not None:
            try:
                animations.evaluate('''entries => entries.forEach(({animation, time, state}) => {
                    animation.currentTime = time;
                    if (state === 'running') animation.play();
                    else if (state === 'idle') animation.cancel();
                    else if (state === 'finished') animation.finish();
                    else animation.pause();
                })''')
            finally:
                animations.dispose()
        session.detach()
