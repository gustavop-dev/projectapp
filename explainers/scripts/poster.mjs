#!/usr/bin/env node
/**
 * Captura el frame de portada del video y lo convierte a WebP 1280x720.
 *
 *   node scripts/poster.mjs --video financing --lang es [--at 4.5]
 */
import { spawnSync } from 'node:child_process'
import { mkdirSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'

import { HYPERFRAMES_BIN, assertExists, parseArgs, requireLanguage, requireVideo, videoDir } from './lib/paths.mjs'

const options = parseArgs(process.argv.slice(2), { defaults: { at: '4.5' } })
const video = requireVideo(options)
const language = requireLanguage(options)
const projectDir = videoDir(video)
const snapshotDir = resolve(projectDir, 'snapshots', 'poster')
const rendersDir = resolve(projectDir, 'renders')
mkdirSync(snapshotDir, { recursive: true })
mkdirSync(rendersDir, { recursive: true })

function run(command, args, extra = {}) {
  const result = spawnSync(command, args, { stdio: 'inherit', ...extra })
  if (result.status !== 0) process.exit(result.status ?? 1)
}

run(process.execPath, [new URL('./sync-assets.mjs', import.meta.url).pathname, '--video', video])
run(process.execPath, [new URL('./stage.mjs', import.meta.url).pathname, '--video', video, '--lang', language])

assertExists(HYPERFRAMES_BIN, 'Corré npm install en explainers/.')
run(HYPERFRAMES_BIN, ['snapshot', '.', '--at', String(options.at), '--no-end', '-o', snapshotDir], {
  cwd: projectDir,
  env: { ...process.env, HYPERFRAMES_NO_TELEMETRY: '1', HYPERFRAMES_NO_UPDATE_CHECK: '1' },
})

const frame = readdirSync(snapshotDir).filter((name) => name.endsWith('.png')).sort().at(-1)
if (!frame) {
  console.error(`hyperframes snapshot no dejó ningún PNG en ${snapshotDir}`)
  process.exit(1)
}

const output = resolve(rendersDir, `${video}-${language}.webp`)
run('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-i', resolve(snapshotDir, frame), '-vf', 'scale=1280:-2', '-c:v', 'libwebp', '-quality', '82', output])
console.log(`Poster: ${output} (desde ${frame})`)
