#!/usr/bin/env node
/**
 * Publica el render final y el poster dentro del frontend (assets con hash,
 * servidos por nginx con cache inmutable).
 *
 *   node scripts/export.mjs --video financing --lang es
 */
import { copyFileSync, mkdirSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

import { FRONTEND_ROOT, assertExists, parseArgs, requireLanguage, requireVideo, videoDir } from './lib/paths.mjs'

const options = parseArgs(process.argv.slice(2), { flags: ['draft'] })
const video = requireVideo(options)
const language = requireLanguage(options)
const rendersDir = resolve(videoDir(video), 'renders')

// --draft publica el render de borrador para integrar el frontend mientras el
// render final espera aprobación; el final lo reemplaza con el mismo comando sin el flag.
const mp4 = assertExists(
  resolve(rendersDir, `${video}-${language}${options.draft ? '.draft' : ''}.mp4`),
  'Renderizá primero con scripts/render.mjs.',
)
const poster = assertExists(resolve(rendersDir, `${video}-${language}.webp`), 'Generá el poster con scripts/poster.mjs.')

const videosDir = resolve(FRONTEND_ROOT, 'assets', 'videos', 'explainers')
const imagesDir = resolve(FRONTEND_ROOT, 'assets', 'images', 'explainers')
mkdirSync(videosDir, { recursive: true })
mkdirSync(imagesDir, { recursive: true })

const mp4Target = resolve(videosDir, `${video}-${language}.mp4`)
const posterTarget = resolve(imagesDir, `${video}-${language}.webp`)
copyFileSync(mp4, mp4Target)
copyFileSync(poster, posterTarget)

const mb = (path) => (statSync(path).size / (1024 * 1024)).toFixed(2)
console.log(`${mp4Target} (${mb(mp4Target)} MB)`)
console.log(`${posterTarget} (${mb(posterTarget)} MB)`)
