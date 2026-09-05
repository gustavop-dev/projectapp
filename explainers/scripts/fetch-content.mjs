#!/usr/bin/env node
/**
 * Descarga el contenido público (catálogo de módulos adicionales y programa de
 * financiación) desde la API de producción y lo congela en content/<video>.<lang>.js
 * para que los renders sean reproducibles sin acceso a la base de datos.
 *
 *   node scripts/fetch-content.mjs --lang es [--origin https://projectapp.co]
 */
import { mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

import { CONTENT_DIR, FRONTEND_ROOT, parseArgs, requireLanguage } from './lib/paths.mjs'

const CONDITION_IDS = ['financing', 'exclusivity', 'calculator', 'hour-package', 'payment-discipline']

const options = parseArgs(process.argv.slice(2), { defaults: { origin: 'https://projectapp.co' } })
const language = requireLanguage(options)
const origin = options.origin.replace(/\/$/, '')

async function fetchJson(path) {
  const url = `${origin}${path}`
  const response = await fetch(url, { headers: { accept: 'application/json' } })
  if (!response.ok) throw new Error(`${url} respondió ${response.status}`)
  return response.json()
}

async function loadLocale(namespace) {
  const file = resolve(FRONTEND_ROOT, 'locales', namespace, `${language}.js`)
  const module = await import(pathToFileURL(file).href)
  return module.default
}

function pick(source, keys) {
  return Object.fromEntries(keys.map((key) => [key, source?.[key] ?? null]))
}

function serialize(payload) {
  return `window.EXPLAINER_CONTENT = ${JSON.stringify(payload, null, 2)};\n`
}

const [catalog, program, catalogLocale, financingLocale] = await Promise.all([
  fetchJson(`/api/additional-modules/public/?lang=${language}`),
  fetchJson(`/api/financing/public/?lang=${language}`),
  loadLocale('additionalModules'),
  loadLocale('financing'),
])

const additionalModules = {
  language,
  generatedAt: new Date().toISOString(),
  totalModules: catalog.total_modules,
  categories: catalog.categories.map((category) => ({
    slug: category.slug,
    name: category.name,
    count: category.modules.length,
    modules: category.modules.map((module) => pick(module, ['slug', 'icon', 'name', 'summary'])),
  })),
  locale: pick(catalogLocale, [
    'eyebrow', 'title', 'subtitle', 'noPriceNotice', 'moduleCount',
    'whatIs', 'purpose', 'problemsSolved', 'integrations', 'requirements', 'downloadPdf',
  ]),
}

const conditions = program.conditions
  .filter((condition) => CONDITION_IDS.includes(condition.id))
  .map((condition) => pick(condition, ['id', 'number', 'icon', 'title']))

const financing = {
  language,
  generatedAt: new Date().toISOString(),
  hero: pick(program.hero, ['eyebrow', 'title', 'subtitle', 'trust_note']),
  eligibility: pick(program.eligibility, ['badge', 'title']),
  conditions,
  options: program.options.map((option) => pick(option, [
    'id', 'badge', 'name', 'recommended', 'exclusivity_years', 'financing_cycles', 'hour_package_included',
  ])),
  package: pick(program.package, ['name', 'hours']),
  cta: pick(program.cta, ['eyebrow', 'title', 'button']),
  financingMonths: program.financing_months,
  ordinaryInterestRate: program.ordinary_interest_rate,
  locale: pick(financingLocale, ['optionsTitle', 'optionsIntro', 'conditionsTitle', 'years', 'downloadPdf']),
}

mkdirSync(CONTENT_DIR, { recursive: true })
writeFileSync(resolve(CONTENT_DIR, `additional-modules.${language}.js`), serialize(additionalModules))
writeFileSync(resolve(CONTENT_DIR, `financing.${language}.js`), serialize(financing))

const manifest = {
  generatedAt: new Date().toISOString(),
  origin,
  language,
  additionalModules: {
    categories: additionalModules.categories.length,
    modules: additionalModules.totalModules,
  },
  financing: {
    conditions: conditions.length,
    options: financing.options.length,
    financingMonths: financing.financingMonths,
  },
}
writeFileSync(resolve(CONTENT_DIR, `manifest.${language}.json`), `${JSON.stringify(manifest, null, 2)}\n`)

console.log(`content/additional-modules.${language}.js → ${manifest.additionalModules.categories} categorías, ${manifest.additionalModules.modules} módulos`)
console.log(`content/financing.${language}.js → ${manifest.financing.conditions} condiciones, ${manifest.financing.options} opciones, ${manifest.financing.financingMonths} meses`)
