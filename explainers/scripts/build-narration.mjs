#!/usr/bin/env node
/**
 * Genera la narración con la voz local (Kokoro vía `hyperframes tts`), una
 * frase por escena, y arma una sola pista alineada a los tiempos de cada escena
 * (leídos del index.html). El resultado se mezcla en render.mjs --with-narration.
 *
 *   node scripts/build-narration.mjs --video financing --lang es --voice em_alex [--speed 1.0]
 *
 * Requiere Kokoro en el PATH (por ejemplo: env PATH=$HOME/.venvs/kokoro/bin:$PATH).
 */
import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

import { AUDIO_DIR, HYPERFRAMES_BIN, TTS_DIR, assertExists, parseArgs, requireLanguage, requireVideo, videoDir } from './lib/paths.mjs'
import { readSchedule } from './lib/schedule.mjs'

const options = parseArgs(process.argv.slice(2), { defaults: { speed: '1.0', lead: '0.6' } })
const video = requireVideo(options)
const language = requireLanguage(options)
const voice = options.voice
if (!voice) {
  console.error('Falta --voice <id> (ver: hyperframes tts --list)')
  process.exit(2)
}

const projectDir = videoDir(video)
const scriptFile = assertExists(resolve(projectDir, `script.${language}.js`))
const { default: script } = await import(pathToFileURL(scriptFile).href)
if (!script?.scenes) {
  console.error(`${scriptFile} no exporta un objeto con "scenes"`)
  process.exit(1)
}

const { scenes } = readSchedule(video)
const ttsDir = resolve(TTS_DIR, video, language)
mkdirSync(ttsDir, { recursive: true })
mkdirSync(AUDIO_DIR, { recursive: true })

function run(command, args, extra = {}) {
  const result = spawnSync(command, args, { stdio: 'inherit', ...extra })
  if (result.status !== 0) process.exit(result.status ?? 1)
}

function durationOf(file) {
  const probe = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file], { encoding: 'utf8' })
  return Number(probe.stdout.trim())
}

const lead = Number(options.lead)
const clips = []
for (const scene of scenes) {
  const text = script.scenes[scene.id]?.narration
  if (!text) continue
  const file = resolve(ttsDir, `${scene.id}.wav`)
  if (!existsSync(file)) {
    run(HYPERFRAMES_BIN, ['tts', text, '--lang', language, '--voice', voice, '--speed', String(options.speed), '-o', file], {
      env: { ...process.env, HYPERFRAMES_NO_TELEMETRY: '1', HYPERFRAMES_NO_UPDATE_CHECK: '1' },
    })
  }
  const duration = durationOf(file)
  const available = scene.duration - lead
  const flag = duration > available ? '  ⚠ excede la escena' : ''
  console.log(`${scene.id.padEnd(22)} ${duration.toFixed(1)}s de ${available.toFixed(1)}s disponibles${flag}`)
  clips.push({ file, offsetMs: Math.round((scene.start + lead) * 1000) })
}

if (!clips.length) {
  console.error('Ninguna escena tiene texto de narración en el guion.')
  process.exit(1)
}

const inputs = clips.flatMap((clip) => ['-i', clip.file])
const delayed = clips.map((clip, index) => `[${index}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=${clip.offsetMs}|${clip.offsetMs}[d${index}]`)
const mix = `${clips.map((_, index) => `[d${index}]`).join('')}amix=inputs=${clips.length}:duration=longest:normalize=0[out]`
const output = resolve(AUDIO_DIR, `${video}-narration-${language}.wav`)
run('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', ...inputs, '-filter_complex', [...delayed, mix].join(';'), '-map', '[out]', output])
console.log(`Narración: ${output} (${clips.length} escenas, voz ${voice})`)
