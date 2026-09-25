#!/usr/bin/env node
/** Local Kokoro narration; content-addressed clips, checked before mixing. */
import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import { EDITION, AUDIO_DIR, HYPERFRAMES_BIN, TTS_DIR, assertExists, parseArgs, requireLanguage, requireVideo, videoDir } from './lib/paths.mjs'
import { narrationKey, assertNarrationFits, captionSchedule, narrationFingerprint } from './lib/narration.mjs'
import { readSchedule } from './lib/schedule.mjs'

const options = parseArgs(process.argv.slice(2), { defaults: { speed: '1.0', lead: '0.6' } })
const video = requireVideo(options)
const language = requireLanguage(options)
const voice = options.voice
if (!voice) throw new Error('Falta --voice <id> (ver: hyperframes tts --list)')
const projectDir = videoDir(video)
const { default: script } = await import(pathToFileURL(assertExists(resolve(projectDir, `script.${language}.js`))).href)
const schedule = readSchedule(video)
const { scenes } = schedule
const ttsDir = resolve(TTS_DIR, video, language)
mkdirSync(ttsDir, { recursive: true })
mkdirSync(AUDIO_DIR, { recursive: true })
function run(command, args) {
  const result = spawnSync(command, args, {
    stdio: 'inherit', env: { ...process.env, HYPERFRAMES_NO_TELEMETRY: '1', HYPERFRAMES_NO_UPDATE_CHECK: '1' },
  })
  if (result.status !== 0) process.exit(result.status ?? 1)
}
function durationOf(file) {
  const result = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file], { encoding: 'utf8' })
  if (result.status !== 0) throw new Error(`Cannot read narration: ${file}`)
  return Number(result.stdout.trim())
}
const lead = Number(options.lead)
if (!Number.isFinite(lead) || lead < 0) throw new Error('Invalid --lead')
const clips = []
const captions = []
for (const scene of scenes) {
  const authored = script.scenes[scene.id]
  if (!authored?.narration) continue
  const segments = authored.voiceSegments || [{ at: 0, text: authored.narration, captions: authored.captions }]
  for (const [index, segment] of segments.entries()) {
    const key = narrationKey({ text: segment.text, voice, language, speed: options.speed })
    const file = resolve(ttsDir, `${scene.id}-${index}-${key}.wav`)
    if (!existsSync(file)) run(HYPERFRAMES_BIN, ['tts', segment.text, '--lang', language, '--voice', voice, '--speed', String(options.speed), '-o', file])
    const duration = durationOf(file)
    const available = (segments[index + 1]?.at ?? scene.duration) - segment.at - lead - 0.3
    assertNarrationFits(duration, available, `${scene.id}/${index}`)
    const offset = scene.start + segment.at + lead
    console.log(`${scene.id}/${index}: ${duration.toFixed(2)}s / ${available.toFixed(2)}s`)
    clips.push({ file, offsetMs: Math.round(offset * 1000) })
    if (EDITION === 'brag-v2') captions.push(...captionSchedule(segment.captions || [segment.text], offset, duration))
  }
}
if (!clips.length) throw new Error('El guion no tiene narración')
const inputs = clips.flatMap((clip) => ['-i', clip.file])
const delayed = clips.map((clip, index) => `[${index}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=${clip.offsetMs}|${clip.offsetMs}[d${index}]`)
const mix = `${clips.map((_, index) => `[d${index}]`).join('')}amix=inputs=${clips.length}:duration=longest:normalize=0[out]`
const output = resolve(AUDIO_DIR, `${video}-narration-${language}.wav`)
run('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...inputs, '-filter_complex', [...delayed, mix].join(';'), '-map', '[out]', output])
if (EDITION === 'brag-v2') writeFileSync(resolve(projectDir, `captions.${language}.json`), JSON.stringify(captions, null, 2) + '\n')
console.log(`Narración: ${output} (${clips.length} segmentos, ${voice})`)

if (EDITION === 'brag-v2') writeFileSync(resolve(AUDIO_DIR, `${video}-narration-${language}.json`), JSON.stringify({ fingerprint: narrationFingerprint(script, schedule), voice, speed: Number(options.speed), lead }, null, 2) + '\n')
