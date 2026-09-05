#!/usr/bin/env node
/**
 * Render final de un video: HyperFrames produce un intermedio casi sin pérdida
 * (la composición es muda) y ffmpeg hace UNA sola codificación final mezclando
 * la música y, si se pide, la narración. Agregar o quitar narración nunca
 * vuelve a renderizar el video.
 *
 *   node scripts/render.mjs --video financing --lang es [--with-narration] [--draft] [--crf 25] [--budget-mb 12]
 */
import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

import { AUDIO_DIR, HYPERFRAMES_BIN, SHARED_DIR, assertExists, parseArgs, requireLanguage, requireVideo, videoDir } from './lib/paths.mjs'
import { readSchedule } from './lib/schedule.mjs'

const options = parseArgs(process.argv.slice(2), {
  defaults: { crf: '25', 'budget-mb': '12', 'music-volume': '0.32', workers: '1' },
  flags: ['with-narration', 'draft', 'skip-render'],
})
const video = requireVideo(options)
const language = requireLanguage(options)
const projectDir = videoDir(video)
const rendersDir = resolve(projectDir, 'renders')
mkdirSync(rendersDir, { recursive: true })

const intermediate = resolve(rendersDir, `${video}-${language}.intermediate.mp4`)
const output = resolve(rendersDir, `${video}-${language}${options.draft ? '.draft' : ''}.mp4`)
const music = resolve(SHARED_DIR, 'music', 'bed.mp3')
const narration = resolve(AUDIO_DIR, `${video}-narration-${language}.wav`)
const { totalDuration } = readSchedule(video)

function run(command, args, extra = {}) {
  const pretty = [command, ...args].map((part) => (/\s/.test(part) ? JSON.stringify(part) : part)).join(' ')
  console.log(`\n$ ${pretty}\n`)
  const result = spawnSync(command, args, { stdio: 'inherit', ...extra })
  if (result.status !== 0) {
    console.error(`${command} terminó con código ${result.status}`)
    process.exit(result.status ?? 1)
  }
}

function runNode(script, args) {
  run(process.execPath, [new URL(script, import.meta.url).pathname, ...args])
}

runNode('./sync-assets.mjs', ['--video', video])
runNode('./stage.mjs', ['--video', video, '--lang', language])

if (!options['skip-render']) {
  assertExists(HYPERFRAMES_BIN, 'Corré npm install en explainers/.')
  const renderArgs = [
    'render', '.',
    '-o', intermediate,
    '--fps', '30',
    '--quality', options.draft ? 'draft' : 'high',
    '--workers', String(options.workers),
    '--strict',
  ]
  if (!options.draft) renderArgs.push('--crf', '18')
  run('nice', ['-n', '15', HYPERFRAMES_BIN, ...renderArgs], {
    cwd: projectDir,
    env: { ...process.env, HYPERFRAMES_NO_TELEMETRY: '1', HYPERFRAMES_NO_UPDATE_CHECK: '1' },
  })
}
assertExists(intermediate, 'El render intermedio no se generó.')

const hasMusic = existsSync(music)
const hasNarration = Boolean(options['with-narration']) && existsSync(narration)
if (options['with-narration'] && !hasNarration) {
  console.error(`Se pidió narración pero no existe ${narration}. Generala con: node scripts/build-narration.mjs --video ${video} --lang ${language} --voice <id>`)
  process.exit(1)
}
if (!hasMusic) console.warn(`Aviso: no hay ${music}; el video saldrá ${hasNarration ? 'sólo con narración' : 'sin audio'}.`)

const inputs = ['-i', intermediate]
const filters = []
let audioLabel = null
const fadeStart = Math.max(0, totalDuration - 4).toFixed(2)

if (hasMusic && hasNarration) {
  inputs.push('-stream_loop', '-1', '-i', music, '-i', narration)
  filters.push(
    `[1:a]atrim=0:${totalDuration},asetpts=PTS-STARTPTS,volume=${options['music-volume']}[music]`,
    '[2:a]aformat=sample_rates=48000:channel_layouts=stereo,apad[voice]',
    '[music][voice]sidechaincompress=threshold=0.03:ratio=8:attack=25:release=450:makeup=1[ducked]',
    '[ducked][2:a]amix=inputs=2:duration=first:normalize=0[mix]',
    `[mix]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st=${fadeStart}:d=4[aout]`,
  )
  audioLabel = '[aout]'
} else if (hasMusic) {
  inputs.push('-stream_loop', '-1', '-i', music)
  filters.push(
    `[1:a]atrim=0:${totalDuration},asetpts=PTS-STARTPTS,volume=${options['music-volume']},loudnorm=I=-18:TP=-1.5:LRA=11,afade=t=out:st=${fadeStart}:d=4[aout]`,
  )
  audioLabel = '[aout]'
} else if (hasNarration) {
  inputs.push('-i', narration)
  filters.push(`[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st=${fadeStart}:d=2[aout]`)
  audioLabel = '[aout]'
}

const ffmpegArgs = ['-y', '-hide_banner', '-loglevel', 'error', '-stats', ...inputs]
if (audioLabel) {
  ffmpegArgs.push('-filter_complex', filters.join(';'), '-map', '0:v:0', '-map', audioLabel)
  ffmpegArgs.push('-c:a', 'aac', '-b:a', '96k', '-ar', '48000', '-ac', '2')
} else {
  ffmpegArgs.push('-map', '0:v:0', '-an')
}
ffmpegArgs.push(
  '-c:v', 'libx264', '-preset', options.draft ? 'veryfast' : 'slow', '-crf', String(options.draft ? 28 : options.crf),
  '-tune', 'animation', '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p',
  '-movflags', '+faststart', '-t', String(totalDuration), output,
)
run('nice', ['-n', '15', 'ffmpeg', ...ffmpegArgs])

const sizeMb = statSync(output).size / (1024 * 1024)
console.log(`\n${output}\n${sizeMb.toFixed(2)} MB · ${totalDuration}s · audio: ${hasMusic ? 'música' : ''}${hasMusic && hasNarration ? ' + ' : ''}${hasNarration ? 'narración' : ''}${!hasMusic && !hasNarration ? 'ninguno' : ''}`)

const budget = Number(options['budget-mb'])
if (!options.draft && sizeMb > budget) {
  console.error(`Excede el presupuesto de ${budget} MB. Reintentá con --crf ${Number(options.crf) + 2} --skip-render (reusa el intermedio).`)
  process.exit(3)
}
