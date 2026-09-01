import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getResponsiveMatrixRows, getResponsiveScenario } from '../responsive/catalog-scenarios.js';

const directory = path.dirname(fileURLToPath(import.meta.url));

/**
 * Records the catalog/profile cells actually executed by Playwright. The
 * declared matrix is the source of truth; the generated JSON is CI evidence
 * only and is intentionally written under e2e-results rather than versioned.
 */
class ResponsiveMatrixReporter {
  constructor(options = {}) {
    this.outputDir = options.outputDir || path.resolve(directory, '../../e2e-results');
    this.batch = process.env.E2E_RESPONSIVE_BATCH || null;
    this.specialOwner = process.env.E2E_RESPONSIVE_SPECIAL_OWNER || null;
    const expectedRows = this.specialOwner
      ? []
      : getResponsiveMatrixRows().filter((row) => !this.batch || row.batch === this.batch);
    this.rows = new Map(expectedRows.map((row) => [
      `${row.catalogKey}::${row.profile}`,
      {
        ...row,
        status: 'no ejecutado',
        result: null,
        test: null,
        attempts: [],
        hadFailure: false,
        testId: null,
      },
    ]));
    this.duplicates = [];
  }

  onTestEnd(test, result) {
    const tags = test.tags || [];
    const scenarioTag = tags.find((tag) => tag.startsWith('@responsive-scenario:'));
    const profileTag = tags.find((tag) => tag.startsWith('@viewport:'));
    if (!scenarioTag || !profileTag) return;

    const catalogKey = scenarioTag.slice('@responsive-scenario:'.length);
    const profile = profileTag.slice('@viewport:'.length);
    const key = `${catalogKey}::${profile}`;
    const row = this.rows.get(key);
    if (!row) {
      this.duplicates.push({ type: 'unknown-cell', catalogKey, profile, title: test.title });
      return;
    }
    if (row.testId && row.testId !== test.id) {
      this.duplicates.push({ type: 'duplicate-cell', catalogKey, profile, title: test.title });
      return;
    }
    row.testId = test.id;
    const isVariant = tags.some((tag) => tag === '@responsive-variant');
    row.attempts.push({ retry: result.retry, status: result.status });
    row.hadFailure ||= result.status !== 'passed';
    row.result = result.status;
    row.status = result.status === 'passed' && !row.hadFailure
      ? (isVariant ? 'cumple distinto' : 'cumple')
      : 'no cumple';
    row.test = { title: test.title, file: test.location.file, retry: result.retry };
  }

  onEnd() {
    const rows = [...this.rows.values()];
    const summary = {
      expected: rows.length,
      executed: rows.filter((row) => row.result !== null).length,
      cumple: rows.filter((row) => row.status === 'cumple').length,
      noCumple: rows.filter((row) => row.status === 'no cumple').length,
      cumpleDistinto: rows.filter((row) => row.status === 'cumple distinto').length,
      flaky: rows.filter((row) => row.result === 'passed' && row.hadFailure).length,
      visual: rows.filter((row) => row.kind === 'visual').length,
      redirect: rows.filter((row) => row.kind === 'redirect').length,
      duplicateOrUnknownCells: this.duplicates.length,
    };
    const report = {
      timestamp: new Date().toISOString(),
      summary,
      duplicates: this.duplicates,
      rows: rows.map(({ testId: _testId, ...row }) => ({
        ...row,
        visualStatus: row.kind === 'redirect' ? 'N/A visual' : row.status,
        scenario: getResponsiveScenario(row.catalogKey)?.label,
      })),
    };
    fs.mkdirSync(this.outputDir, { recursive: true });
    fs.writeFileSync(path.join(this.outputDir, 'responsive-matrix.json'), JSON.stringify(report, null, 2));
    console.log(`Responsive matrix: ${summary.executed}/${summary.expected} executed · ${summary.cumple} cumple · ${summary.noCumple} no cumple · ${summary.cumpleDistinto} cumple distinto · ${summary.flaky} flaky.`);
    if (summary.executed !== summary.expected || summary.noCumple > 0 || summary.duplicateOrUnknownCells > 0) {
      return { status: 'failed' };
    }
    return { status: 'passed' };
  }
}

export default ResponsiveMatrixReporter;
