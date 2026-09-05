#!/usr/bin/env node
/**
 * Prepara la raíz del proyecto HyperFrames para un idioma: copia el contenido
 * congelado (content.js) y convierte el guion ESM (script.<lang>.js) en el
 * global que lee la composición (script.js). Ambos archivos están gitignored.
 *
 *   node scripts/stage.mjs --video financing --lang es
 */
import { copyFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

import { CONTENT_DIR, assertExists, parseArgs, requireLanguage, requireVideo, videoDir } from './lib/paths.mjs'

const options = parseArgs(process.argv.slice(2))
const video = requireVideo(options)
const language = requireLanguage(options)
const projectDir = videoDir(video)

const contentSource = assertExists(
  resolve(CONTENT_DIR, `${video}.${language}.js`),
  `Generalo con: node scripts/fetch-content.mjs --lang ${language}`,
)
const scriptSource = assertExists(
  resolve(projectDir, `script.${language}.js`),
  `Escribí el guion ${video}/script.${language}.js antes de preparar el proyecto.`,
)

const { default: script } = await import(pathToFileURL(scriptSource).href)
if (!script || typeof script !== 'object' || !script.scenes) {
  throw new Error(`${scriptSource} debe exportar por default un objeto con "scenes"`)
}

copyFileSync(contentSource, resolve(projectDir, 'content.js'))
writeFileSync(resolve(projectDir, 'script.js'), `window.EXPLAINER_SCRIPT = ${JSON.stringify(script, null, 2)};\n`)
console.log(`${video}: content.js y script.js preparados para "${language}"`)
