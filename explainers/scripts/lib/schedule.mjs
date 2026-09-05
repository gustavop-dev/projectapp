import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { videoDir } from './paths.mjs'

const SECTION_PATTERN = /<section\b[^>]*\bclass="[^"]*\bclip\b[^"]*"[^>]*>/g

function attribute(tag, name) {
  const match = tag.match(new RegExp(`\\b${name}="([^"]*)"`))
  return match ? match[1] : null
}

/**
 * Reads the scene schedule straight from the composition markup so every tool
 * (timeline, narration builder, poster) shares the same timing source.
 */
export function readSchedule(video) {
  const html = readFileSync(resolve(videoDir(video), 'index.html'), 'utf8')
  const rootMatch = html.match(/<div\b[^>]*\bid="root"[^>]*>/)
  if (!rootMatch) throw new Error(`index.html de ${video} no tiene un <div id="root">`)
  const totalDuration = Number(attribute(rootMatch[0], 'data-duration'))
  const fps = Number(attribute(rootMatch[0], 'data-fps') || 30)

  const scenes = []
  for (const tag of html.match(SECTION_PATTERN) || []) {
    const id = attribute(tag, 'id')
    const start = Number(attribute(tag, 'data-start'))
    const duration = Number(attribute(tag, 'data-duration'))
    if (!id || Number.isNaN(start) || Number.isNaN(duration)) continue
    scenes.push({ id, start, duration, end: start + duration })
  }
  scenes.sort((left, right) => left.start - right.start)

  if (!scenes.length) throw new Error(`index.html de ${video} no declara escenas .clip con data-start/data-duration`)
  return { totalDuration, fps, scenes }
}
