#!/usr/bin/env node
/**
 * Ejecuta un subcomando del CLI de HyperFrames con el proyecto del video como
 * cwd, después de sincronizar assets y preparar contenido/guion.
 *
 *   node scripts/run.mjs lint --video financing
 *   node scripts/run.mjs check --video financing --snapshots
 *   node scripts/run.mjs snapshot --video financing --at 3,10,20
 *   node scripts/run.mjs preview --video financing --port 3002
 */
import { spawnSync } from 'node:child_process'

import { HYPERFRAMES_BIN, assertExists, parseArgs, requireLanguage, requireVideo, videoDir } from './lib/paths.mjs'

const [command, ...rest] = process.argv.slice(2)
const ALLOWED = ['lint', 'check', 'snapshot', 'preview', 'info', 'compositions', 'keyframes']
if (!ALLOWED.includes(command)) {
  console.error(`Uso: node scripts/run.mjs <${ALLOWED.join('|')}> --video <id> [--lang es] [flags del CLI]`)
  process.exit(2)
}

const options = parseArgs(rest, { flags: ['snapshots', 'strict', 'verbose', 'json', 'no-end', 'background', 'no-open', 'open'] })
const video = requireVideo(options)
const language = requireLanguage(options)
const projectDir = videoDir(video)

function runNode(script, args) {
  // Con --json el stdout debe quedar limpio para que el llamador lo parsee.
  const stdio = options.json ? ['inherit', 'ignore', 'inherit'] : 'inherit'
  const result = spawnSync(process.execPath, [script, ...args], { stdio })
  if (result.status !== 0) process.exit(result.status ?? 1)
}

runNode(new URL('./sync-assets.mjs', import.meta.url).pathname, ['--video', video])
runNode(new URL('./stage.mjs', import.meta.url).pathname, ['--video', video, '--lang', language])

const passthrough = []
for (const [key, value] of Object.entries(options)) {
  if (['video', 'lang', '_'].includes(key)) continue
  if (value === true) passthrough.push(`--${key}`)
  else passthrough.push(`--${key}`, String(value))
}

assertExists(HYPERFRAMES_BIN, 'Corré npm install en explainers/.')
const result = spawnSync(HYPERFRAMES_BIN, [command, '.', ...passthrough], {
  cwd: projectDir,
  stdio: 'inherit',
  env: { ...process.env, HYPERFRAMES_NO_TELEMETRY: '1', HYPERFRAMES_NO_UPDATE_CHECK: '1' },
})
process.exit(result.status ?? 1)
