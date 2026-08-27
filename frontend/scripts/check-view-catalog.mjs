import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  VIEW_AUDIENCES,
  VIEW_TYPES,
  viewCatalogSections,
} from '../config/viewCatalog.js'
import {
  auditViewCatalog,
  catalogAuditFindings,
} from '../config/viewCatalogAudit.js'
import { capabilityCatalogFindings } from '../config/viewCapabilityCatalog.js'

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const pagesRoot = path.join(frontendRoot, 'pages')

function walk(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const absolutePath = path.join(directory, entry.name)
    return entry.isDirectory() ? walk(absolutePath) : [absolutePath]
  })
}

const pageFiles = walk(pagesRoot)
  .filter((file) => file.endsWith('.vue'))
  .filter((file) => !path.basename(file).startsWith('_'))
  .filter((file) => !file.includes(`${path.sep}__tests__${path.sep}`))
  .filter((file) => !file.includes(`${path.sep}components${path.sep}`))
  .filter((file) => path.basename(file) !== 'error.vue')
  .map((file) => `frontend/${path.relative(frontendRoot, file).split(path.sep).join('/')}`)

const audit = auditViewCatalog({
  pageFiles,
  sections: viewCatalogSections,
  validAudiences: VIEW_AUDIENCES,
  validViewTypes: VIEW_TYPES,
})
const findings = [
  ...catalogAuditFindings(audit),
  ...capabilityCatalogFindings(),
]

if (findings.length > 0) {
  console.error(`View catalog check failed with ${findings.length} finding(s):`)
  for (const finding of findings) console.error(`- ${finding}`)
  process.exitCode = 1
} else {
  console.log(
    `View catalog OK: ${audit.pageCount} pages, ${audit.entryCount} entries, operational taxonomy valid.`,
  )
}
