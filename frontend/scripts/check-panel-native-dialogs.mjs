#!/usr/bin/env node

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const roots = [
  path.join(frontendRoot, 'pages/panel'),
  path.join(frontendRoot, 'components/panel'),
]
const nativeNames = ['alert', 'confirm', 'prompt']

function walk(target) {
  if (!fs.existsSync(target)) return []
  const stat = fs.statSync(target)
  if (stat.isFile()) return /\.(?:vue|[jt]sx?)$/.test(target) ? [target] : []
  return fs.readdirSync(target).flatMap((entry) => walk(path.join(target, entry)))
}

function lineNumber(source, offset) {
  return source.slice(0, offset).split('\n').length
}

function scriptBlocks(source, filename) {
  if (!filename.endsWith('.vue')) return [{ code: source, offset: 0 }]
  const blocks = []
  const pattern = /<script\b[^>]*>([\s\S]*?)<\/script>/g
  for (const match of source.matchAll(pattern)) {
    blocks.push({
      code: match[1],
      offset: match.index + match[0].indexOf(match[1]),
    })
  }
  return blocks
}

// Remove comments and quoted text while preserving offsets/newlines. The
// guard is interested in executable calls, not examples in copy or comments.
function executableMask(source) {
  const chars = [...source]
  let state = 'code'
  let quote = ''
  for (let index = 0; index < chars.length; index += 1) {
    const current = chars[index]
    const next = chars[index + 1]
    if (state === 'line-comment') {
      if (current === '\n') state = 'code'
      else chars[index] = ' '
      continue
    }
    if (state === 'block-comment') {
      if (current === '*' && next === '/') {
        chars[index] = ' '
        chars[index + 1] = ' '
        index += 1
        state = 'code'
      } else if (current !== '\n') chars[index] = ' '
      continue
    }
    if (state === 'string') {
      if (current === '\\') {
        chars[index] = ' '
        if (chars[index + 1] !== '\n') chars[index + 1] = ' '
        index += 1
      } else if (current === quote) {
        chars[index] = ' '
        state = 'code'
      } else if (current !== '\n') chars[index] = ' '
      continue
    }
    if (current === '/' && next === '/') {
      chars[index] = ' '
      chars[index + 1] = ' '
      index += 1
      state = 'line-comment'
    } else if (current === '/' && next === '*') {
      chars[index] = ' '
      chars[index + 1] = ' '
      index += 1
      state = 'block-comment'
    } else if (current === '"' || current === "'" || current === '`') {
      quote = current
      chars[index] = ' '
      state = 'string'
    }
  }
  return chars.join('')
}

function locallyDeclared(code, name) {
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return [
    new RegExp(`\\bfunction\\s+${escaped}\\b`),
    new RegExp(`\\b(?:const|let|var|class)\\s+${escaped}\\b`),
    new RegExp(`\\bimport\\s+${escaped}\\b`),
    new RegExp(`\\bimport\\s*\\{[^}]*\\b${escaped}\\b[^}]*\\}`),
  ].some((pattern) => pattern.test(code))
}

function findingsForCode(code) {
  const masked = executableMask(code)
  const findings = []
  const memberPattern = /\b(?:window|globalThis)\s*(?:\.\s*(alert|confirm|prompt)|\[\s*['"](alert|confirm|prompt)['"]\s*\])\s*\(/g
  for (const match of masked.matchAll(memberPattern)) {
    findings.push({ name: match[1] || match[2], offset: match.index })
  }
  for (const name of nativeNames) {
    if (locallyDeclared(masked, name)) continue
    const globalPattern = new RegExp(`(?<![\\w.$])${name}\\s*\\(`, 'g')
    for (const match of masked.matchAll(globalPattern)) {
      findings.push({ name, offset: match.index })
    }
  }
  return findings.filter((finding, index, all) => (
    all.findIndex((candidate) => candidate.offset === finding.offset) === index
  ))
}

// A local helper may legitimately be named `confirm`; it is not a browser
// dialog and must never make the repository gate noisy.
if (findingsForCode('function confirm(value) { return value }\nconfirm(true)').length) {
  throw new Error('Panel native-dialog guard self-test failed for local bindings.')
}

const errors = []
const files = [...new Set(roots.flatMap(walk))].sort()
for (const file of files) {
  const source = fs.readFileSync(file, 'utf8')
  for (const block of scriptBlocks(source, file)) {
    for (const finding of findingsForCode(block.code)) {
      const absoluteOffset = block.offset + finding.offset
      errors.push(
        `${path.relative(frontendRoot, file)}:${lineNumber(source, absoluteOffset)} uses browser ${finding.name}()`,
      )
    }
  }
}

if (errors.length) {
  console.error('Panel native-dialog guard failed:')
  for (const error of errors) console.error(`  - ${error}`)
  console.error('\nUse BaseModal or ConfirmModal for panel interactions.')
  process.exit(1)
}

console.log(`Panel native-dialog guard passed (${files.length} files).`)
