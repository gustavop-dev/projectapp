import { createHash } from 'node:crypto'

export function narrationKey({ text, voice, language, speed }) {
  return createHash('sha256').update(JSON.stringify({ text, voice, language, speed: Number(speed) })).digest('hex').slice(0, 20)
}

export function assertNarrationFits(duration, available, sceneId) {
  if (!Number.isFinite(duration) || duration <= 0) throw new Error(`Invalid narration duration: ${sceneId}`)
  if (duration > available) throw new Error(`Narration exceeds ${sceneId}: ${duration.toFixed(2)}s > ${available.toFixed(2)}s; shorten the script or extend the scene.`)
}

export function captionSchedule(captions, start, duration) {
  const weights = captions.map((text) => text.trim().split(/\s+/).length)
  const total = weights.reduce((sum, weight) => sum + weight, 0)
  let cursor = start
  return captions.map((text, index) => {
    const span = duration * weights[index] / total
    const cue = { text, start: cursor, end: cursor + span }
    cursor += span
    return cue
  })
}

export function narrationFingerprint(script, schedule) {
  return createHash('sha256').update(JSON.stringify({ scenes: script.scenes, schedule })).digest('hex')
}
