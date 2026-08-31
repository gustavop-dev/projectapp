#!/usr/bin/env node
/**
 * Cross-application icon interaction guard.
 *
 * An icon-only executable control must pass through BaseButton (or the panel's
 * BaseActionButton) so pointer, touch, keyboard and reduced-motion feedback do
 * not drift by surface. Text buttons, decorative icons and base primitives are
 * intentionally outside this syntactic check.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const roots = ['components', 'layouts', 'pages']
const controlPattern = /<(button|a|NuxtLink)\b[\s\S]*?<\/\1>/g
const allowPattern = /icon-interaction-feedback:\s*allow-custom\s+--\s*[^\n]+/
const srOnlyPattern = /<([a-z][\w-]*)\b[^>]*class=["'][^"']*\bsr-only\b[^"']*["'][^>]*>[\s\S]*?<\/\1>/gi

function walk(target) {
  if (!fs.existsSync(target)) return []
  const stat = fs.statSync(target)
  if (stat.isFile()) return target.endsWith('.vue') ? [target] : []
  return fs.readdirSync(target).flatMap((entry) => walk(path.join(target, entry)))
}

function lineNumber(source, offset) {
  return source.slice(0, offset).split('\n').length
}

function hasAllowComment(source, offset) {
  return allowPattern.test(source.slice(Math.max(0, offset - 320), offset))
}

function hasVisibleLabel(block) {
  const body = block.slice(block.indexOf('>') + 1, block.lastIndexOf('</'))
  if (/<slot\b/.test(body) || /{{[\s\S]*?}}/.test(body)) return true

  const text = body
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(srOnlyPattern, '')
    .replace(/<[^>]+>/g, '')
    .replace(/&(?:[a-z]+|#\d+|#x[\da-f]+);/gi, '')
    .trim()

  return /[\p{L}\p{N}]/u.test(text)
}

const files = roots
  .flatMap((entry) => walk(path.join(frontendRoot, entry)))
  .filter((file) => !file.includes(`${path.sep}components${path.sep}base${path.sep}`))
  .sort()
const errors = []

for (const file of files) {
  const source = fs.readFileSync(file, 'utf8')
  for (const match of source.matchAll(controlPattern)) {
    if (hasVisibleLabel(match[0]) || hasAllowComment(source, match.index)) continue
    errors.push(
      `${path.relative(frontendRoot, file)}:${lineNumber(source, match.index)} uses a raw icon-only <${match[1]}>`,
    )
  }
}

if (errors.length) {
  console.error('Icon interaction feedback guard failed:')
  errors.forEach((error) => console.error(`  - ${error}`))
  console.error('\nUse BaseButton icon-only or BaseActionButton. Bespoke controls require:')
  console.error('<!-- icon-interaction-feedback: allow-custom -- <specific reason> -->')
  process.exit(1)
}

console.log(`Icon interaction feedback guard passed (${files.length} application Vue files).`)
