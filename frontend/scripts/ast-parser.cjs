#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { parse } = require('@babel/parser');

const filePath = process.argv[2];
const isE2E = process.argv.includes('--e2e');

if (!filePath) {
  process.stdout.write(JSON.stringify({ error: 'No file path provided' }));
  process.exit(1);
}

let source;
try {
  source = fs.readFileSync(path.resolve(filePath), 'utf-8');
} catch (err) {
  process.stdout.write(JSON.stringify({ error: `Cannot read file: ${err.message}` }));
  process.exit(1);
}

let ast;
try {
  ast = parse(source, {
    sourceType: 'module',
    plugins: ['jsx', 'typescript', 'decorators-legacy', 'dynamicImport', 'classProperties', 'optionalChaining', 'nullishCoalescingOperator'],
    errorRecovery: true,
  });
} catch (err) {
  process.stdout.write(JSON.stringify({
    file: filePath,
    tests: [],
    issues: [{ type: 'PARSE_ERROR', message: `Babel parse error: ${err.message}`, line: err.loc ? err.loc.line : 1 }],
    summary: { testCount: 0, issueCount: 1, hasParseError: true },
  }));
  process.exit(0);
}

const lines = source.split('\n');
const tests = [];
const issues = [];
const describeStack = [];
const seenTestNames = new Map();

const BANNED_TOKENS = ['batch', 'coverage', 'cov', 'deep'];
const GENERIC_TITLES = [
  'it works', 'should work', 'test', 'works', 'does something',
  'handles it', 'is correct', 'passes', 'runs',
];
const ASSERTION_PATTERNS = [
  /\bexpect\s*\(/,
  /\bassert\b/,
  /\.toBeVisible\b/,
  /\.toBeHidden\b/,
  /\.toHaveText\b/,
  /\.toHaveURL\b/,
  /\.toHaveTitle\b/,
  /\.toContainText\b/,
  /\.toBeAttached\b/,
  /\.toBeChecked\b/,
  /\.toBeEnabled\b/,
  /\.toBeDisabled\b/,
  /\.toHaveValue\b/,
  /\.toHaveCount\b/,
  /\.toHaveAttribute\b/,
  /\.toHaveClass\b/,
  /\.toHaveCSS\b/,
];
const CONSOLE_LOG_PATTERN = /\bconsole\s*\.\s*log\s*\(/;
const WAIT_FOR_TIMEOUT_PATTERN = /\.waitForTimeout\s*\(\s*(\d+)\s*\)/;
const USELESS_ASSERTIONS = [
  'expect(true).toBe(true)',
  'expect(1).toBe(1)',
  'expect(true).toBeTruthy()',
  'expect(false).toBeFalsy()',
];

function getSourceRange(node) {
  const startLine = node.loc ? node.loc.start.line : 0;
  const endLine = node.loc ? node.loc.end.line : 0;
  return { startLine, endLine, numLines: endLine - startLine + 1 };
}

function getBodySource(node) {
  const { startLine, endLine } = getSourceRange(node);
  return lines.slice(startLine - 1, endLine).join('\n');
}

function isCallTo(node, names) {
  if (!node || node.type !== 'CallExpression') return null;
  const callee = node.callee;
  if (callee.type === 'Identifier' && names.includes(callee.name)) return callee.name;
  if (callee.type === 'MemberExpression' && callee.object.type === 'Identifier' && names.includes(callee.object.name)) {
    const prop = callee.property.name || callee.property.value;
    if (['skip', 'only', 'todo', 'serial'].includes(prop)) return callee.object.name;
  }
  return null;
}

function isSkipped(node) {
  const callee = node.callee;
  if (callee.type === 'MemberExpression') {
    const prop = callee.property.name || callee.property.value;
    return prop === 'skip' || prop === 'todo';
  }
  return false;
}

function isOnly(node) {
  const callee = node.callee;
  if (callee.type === 'MemberExpression') {
    const prop = callee.property.name || callee.property.value;
    return prop === 'only';
  }
  return false;
}

function getTestName(node) {
  const args = node.arguments;
  if (!args || args.length === 0) return '';
  const first = args[0];
  if (first.type === 'StringLiteral') return first.value;
  if (first.type === 'TemplateLiteral' && first.quasis.length > 0) {
    return first.quasis.map(q => q.value.cooked || q.value.raw).join('*');
  }
  return '';
}

function getTestBody(node) {
  const args = node.arguments;
  for (let i = 1; i < args.length; i++) {
    if (args[i].type === 'ArrowFunctionExpression' || args[i].type === 'FunctionExpression') {
      return args[i];
    }
  }
  if (args.length >= 3 && args[1].type === 'ObjectExpression') {
    const fn = args[2];
    if (fn && (fn.type === 'ArrowFunctionExpression' || fn.type === 'FunctionExpression')) {
      return fn;
    }
  }
  return null;
}

function analyzeBody(bodyNode, bodySource) {
  let assertionCount = 0;
  let hasConsoleLog = false;
  let hasHardcodedTimeout = false;
  let timeoutValue = 0;
  const bodyLines = bodySource.split('\n');

  for (const line of bodyLines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('//') || trimmed.startsWith('/*')) continue;

    for (const pat of ASSERTION_PATTERNS) {
      if (pat.test(trimmed)) { assertionCount++; break; }
    }
    if (CONSOLE_LOG_PATTERN.test(trimmed)) hasConsoleLog = true;

    const timeoutMatch = WAIT_FOR_TIMEOUT_PATTERN.exec(trimmed);
    if (timeoutMatch) {
      hasHardcodedTimeout = true;
      timeoutValue = parseInt(timeoutMatch[1], 10);
    }
  }

  const isEmpty = bodyNode && bodyNode.body &&
    ((bodyNode.body.type === 'BlockStatement' && bodyNode.body.body.length === 0) ||
     (Array.isArray(bodyNode.body) && bodyNode.body.length === 0));

  return { assertionCount, hasAssertions: assertionCount > 0, hasConsoleLog, hasHardcodedTimeout, timeoutValue, isEmpty: !!isEmpty };
}

function checkUselessAssertions(bodySource, line, testName) {
  const found = [];
  for (const ua of USELESS_ASSERTIONS) {
    if (bodySource.includes(ua)) {
      found.push({
        type: 'USELESS_ASSERTION',
        message: `Useless assertion: "${ua}"`,
        line,
        identifier: testName,
        suggestion: 'Replace with meaningful assertion that tests actual behavior',
      });
    }
  }
  return found;
}

function checkNaming(name, line) {
  const found = [];
  const lower = name.toLowerCase();

  const bannedWordChecks = [
    { re: /\bbatch\b/i, token: 'batch' },
    { re: /\bcoverage\b/i, token: 'coverage' },
    { re: /\bcov\b/i, token: 'cov' },
    { re: /\bdeep\b/i, token: 'deep' },
  ];
  for (const { re, token } of bannedWordChecks) {
    if (re.test(lower)) {
      found.push({
        type: 'FORBIDDEN_TOKEN',
        message: `Forbidden token "${token}" in test name: "${name}"`,
        line,
        identifier: name,
        suggestion: 'Remove forbidden token and use a behavior-describing name',
      });
    }
  }

  for (const generic of GENERIC_TITLES) {
    if (lower === generic) {
      found.push({
        type: 'POOR_NAMING',
        message: `Generic test name: "${name}"`,
        line,
        identifier: name,
        suggestion: "Use descriptive name: 'should <action> when <condition>'",
      });
    }
  }

  return found;
}

const handledNodes = new WeakSet();

function walk(node, visitor) {
  if (!node || typeof node !== 'object') return;
  if (handledNodes.has(node)) return;
  if (Array.isArray(node)) {
    for (const child of node) walk(child, visitor);
    return;
  }
  if (node.type) visitor(node);
  for (const key of Object.keys(node)) {
    if (key === 'leadingComments' || key === 'trailingComments' || key === 'innerComments') continue;
    if (key === 'loc' || key === 'start' || key === 'end') continue;
    const child = node[key];
    if (child && typeof child === 'object') walk(child, visitor);
  }
}

function visitNode(node) {
  if (node.type !== 'ExpressionStatement') return;
  const callExpr = node.expression;
  if (!callExpr || callExpr.type !== 'CallExpression') return;

  const describeMatch = isCallTo(callExpr, ['describe']);
  if (describeMatch) {
    const name = getTestName(callExpr);
    describeStack.push(name);
    const bodyFn = getTestBody(callExpr);
    if (bodyFn) {
      handledNodes.add(bodyFn);
      walk(bodyFn.body, visitNode);
    }
    describeStack.pop();
    return;
  }

  const testMatch = isCallTo(callExpr, ['it', 'test']);
  if (!testMatch) return;

  const name = getTestName(callExpr);
  const bodyFn = getTestBody(callExpr);
  const { startLine, endLine, numLines } = getSourceRange(callExpr);
  const describeBlock = describeStack.length > 0 ? describeStack[describeStack.length - 1] : null;
  const fullContext = describeBlock ? `${describeBlock} > ${name}` : name;

  let bodyAnalysis = { assertionCount: 0, hasAssertions: false, hasConsoleLog: false, hasHardcodedTimeout: false, timeoutValue: 0, isEmpty: false };
  let bodySource = '';
  if (bodyFn) {
    bodySource = getBodySource(bodyFn);
    bodyAnalysis = analyzeBody(bodyFn, bodySource);
  }

  const testInfo = {
    name,
    fullContext,
    line: startLine,
    endLine,
    numLines,
    type: testMatch,
    isSkipped: isSkipped(callExpr),
    isOnly: isOnly(callExpr),
    hasAssertions: bodyAnalysis.hasAssertions,
    assertionCount: bodyAnalysis.assertionCount,
    hasConsoleLog: bodyAnalysis.hasConsoleLog,
    hasHardcodedTimeout: bodyAnalysis.hasHardcodedTimeout,
    timeoutValue: bodyAnalysis.timeoutValue,
    isEmpty: bodyAnalysis.isEmpty,
    describeBlock,
  };
  tests.push(testInfo);

  if (bodyAnalysis.isEmpty) {
    issues.push({ type: 'EMPTY_TEST', message: `Empty test body: "${name}"`, line: startLine, identifier: name });
  } else if (!bodyAnalysis.hasAssertions && !isE2E) {
    issues.push({ type: 'NO_ASSERTIONS', message: `No assertions found in: "${name}"`, line: startLine, identifier: name, suggestion: 'Add expect() assertions to verify behavior' });
  }

  if (bodyAnalysis.hasConsoleLog) {
    issues.push({ type: 'CONSOLE_LOG', message: `console.log found in: "${name}"`, line: startLine, identifier: name, suggestion: 'Remove console.log (use debugger or test reporter)' });
  }

  if (bodyAnalysis.hasHardcodedTimeout) {
    const issueType = isE2E ? 'WAIT_FOR_TIMEOUT' : 'HARDCODED_TIMEOUT';
    issues.push({ type: issueType, message: `waitForTimeout(${bodyAnalysis.timeoutValue}) in: "${name}"`, line: startLine, identifier: name, suggestion: 'Use condition-based waits instead of fixed timeouts' });
  }

  if (bodyAnalysis.assertionCount > 7) {
    issues.push({ type: 'TOO_MANY_ASSERTIONS', message: `${bodyAnalysis.assertionCount} assertions in: "${name}" (max 7)`, line: startLine, identifier: name, suggestion: 'Split into multiple focused tests' });
  }

  if (numLines > 50) {
    issues.push({ type: 'TEST_TOO_LONG', message: `Test is ${numLines} lines (max 50): "${name}"`, line: startLine, identifier: name, suggestion: 'Extract setup to helpers or split test' });
  }

  issues.push(...checkNaming(name, startLine));
  issues.push(...checkUselessAssertions(bodySource, startLine, name));

  const dupeKey = describeBlock ? `${describeBlock}::${name}` : name;
  if (seenTestNames.has(dupeKey)) {
    issues.push({ type: 'DUPLICATE_NAME', message: `Duplicate test name: "${name}"`, line: startLine, identifier: name, suggestion: 'Rename to be unique within describe block' });
  } else {
    seenTestNames.set(dupeKey, startLine);
  }
}

walk(ast.program, visitNode);

const output = {
  file: filePath,
  tests,
  issues,
  summary: {
    testCount: tests.length,
    issueCount: issues.length,
    hasParseError: false,
  },
};

process.stdout.write(JSON.stringify(output));
