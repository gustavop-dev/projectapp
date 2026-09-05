import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export const EXPLAINERS_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')
export const REPO_ROOT = resolve(EXPLAINERS_ROOT, '..')
export const FRONTEND_ROOT = resolve(REPO_ROOT, 'frontend')
export const SHARED_DIR = resolve(EXPLAINERS_ROOT, 'shared')
export const CONTENT_DIR = resolve(EXPLAINERS_ROOT, 'content')
export const AUDIO_DIR = resolve(EXPLAINERS_ROOT, 'audio')
export const TTS_DIR = resolve(EXPLAINERS_ROOT, 'tts')
export const HYPERFRAMES_BIN = resolve(EXPLAINERS_ROOT, 'node_modules', '.bin', 'hyperframes')

export const VIDEOS = Object.freeze(['additional-modules', 'financing'])
export const LANGUAGES = Object.freeze(['es', 'en'])

export function parseArgs(argv, { defaults = {}, flags = [] } = {}) {
  const options = { ...defaults, _: [] }
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index]
    if (!token.startsWith('--')) {
      options._.push(token)
      continue
    }
    const key = token.slice(2)
    if (flags.includes(key)) {
      options[key] = true
      continue
    }
    const next = argv[index + 1]
    if (next === undefined || next.startsWith('--')) {
      options[key] = true
      continue
    }
    options[key] = next
    index += 1
  }
  return options
}

export function requireVideo(options) {
  const video = options.video || options._[0]
  if (!VIDEOS.includes(video)) {
    throw new Error(`--video debe ser uno de: ${VIDEOS.join(', ')} (recibido: ${video ?? 'nada'})`)
  }
  return video
}

export function requireLanguage(options) {
  const language = options.lang || 'es'
  if (!LANGUAGES.includes(language)) {
    throw new Error(`--lang debe ser uno de: ${LANGUAGES.join(', ')} (recibido: ${language})`)
  }
  return language
}

export function videoDir(video) {
  return resolve(EXPLAINERS_ROOT, video)
}

export function assertExists(path, hint) {
  if (!existsSync(path)) {
    throw new Error(`No existe ${path}. ${hint ?? ''}`.trim())
  }
  return path
}
