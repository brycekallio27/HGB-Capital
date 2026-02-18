# Testing Patterns

**Analysis Date:** 2026-02-18

## Test Framework

**Runner:**
- Node.js built-in `node:test` module (no external test runner)
- Config: none (invoked directly via `node --test`)
- Located in: `get-shit-done/get-shit-done/bin/gsd-tools.test.cjs`

**Assertion Library:**
- Node.js built-in `node:assert` (strict mode)

**Run Commands:**
```bash
# From get-shit-done/ directory
npm test                                                     # Run all tests
node --test get-shit-done/bin/gsd-tools.test.js             # Run directly
```

**Build Tools:**
- `ui-ux-pro-max-skill/cli`: Bun (build only, no test runner configured)
  - `bun build src/index.ts --outdir dist --target node`
  - No test scripts in `cli/package.json`

## Test File Organization

**Location:**
- Co-located with implementation: `gsd-tools.test.cjs` lives alongside `gsd-tools.cjs` in `get-shit-done/get-shit-done/bin/`
- Tests written in CommonJS (`.cjs`) to match the runtime environment

**Naming:**
- Pattern: `<name>.test.cjs`
- Single test file per module (one test file for the entire `gsd-tools.cjs` CLI)

**Structure:**
```
get-shit-done/
└── get-shit-done/
    └── bin/
        ├── gsd-tools.cjs         # Implementation
        └── gsd-tools.test.cjs    # Tests
```

## Test Structure

**Suite Organization:**
```javascript
const { test, describe, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');

describe('history-digest command', () => {
  let tmpDir;

  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('empty phases directory returns valid schema', () => {
    const result = runGsdTools('history-digest', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    const digest = JSON.parse(result.output);
    assert.deepStrictEqual(digest.phases, {}, 'phases should be empty object');
  });
});
```

**Patterns:**
- `describe()` groups tests by CLI command/subcommand
- `beforeEach()` creates a fresh temp directory with required structure
- `afterEach()` removes temp directory unconditionally
- Each test is self-contained: creates its own fixture files, runs command, asserts output

## Mocking

**Framework:** None. Tests use real filesystem via temp directories.

**Integration approach:**
- No mocking of modules or functions
- Tests invoke the CLI binary directly via `execSync()`
- Filesystem state is real (created in OS temp dir, cleaned up after each test)
- Network calls are not present in tested code (gsd-tools.cjs is filesystem-only)

**What is tested without mocks:**
- CLI command parsing and routing
- File system reading and writing
- YAML frontmatter parsing
- JSON output format and schema

**What is NOT mocked:**
- Nothing is mocked — all tests are integration-style against real filesystem

## Fixtures and Factories

**Test Data:**
```javascript
// Helper to create a standard project structure
function createTempProject() {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gsd-test-'));
  fs.mkdirSync(path.join(tmpDir, '.planning', 'phases'), { recursive: true });
  return tmpDir;
}

// Individual test fixtures created inline
fs.writeFileSync(path.join(phaseDir, '01-01-SUMMARY.md'), `---
phase: "01"
name: "Foundation Setup"
provides:
  - "Database schema"
---
`);
```

**Location:**
- No separate fixtures directory; all fixture data is created inline within each test
- Fixtures use template literals for YAML/Markdown content
- All fixtures live in OS `tmpdir()` and are cleaned up by `afterEach`

## Coverage

**Requirements:** None enforced (no coverage tooling configured)

**View Coverage:**
```bash
# Not configured
```

## Test Types

**Unit Tests:**
- Not present as standalone unit tests

**Integration Tests:**
- Primary test style: CLI integration tests
- Each test invokes `gsd-tools.cjs` as a subprocess via `execSync()`
- Tests verify JSON output schema and content
- Tests verify behavior with edge cases: empty dirs, malformed YAML, multiple phases

**E2E Tests:**
- Not used

## Common Patterns

**CLI subprocess invocation:**
```javascript
function runGsdTools(args, cwd = process.cwd()) {
  try {
    const result = execSync(`node "${TOOLS_PATH}" ${args}`, {
      cwd,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { success: true, output: result.trim() };
  } catch (err) {
    return {
      success: false,
      output: err.stdout?.toString().trim() || '',
      error: err.stderr?.toString().trim() || err.message,
    };
  }
}
```

**Asserting success before parsing JSON:**
```javascript
const result = runGsdTools('history-digest', tmpDir);
assert.ok(result.success, `Command failed: ${result.error}`);
const digest = JSON.parse(result.output);
```

**Error/edge case testing:**
```javascript
test('malformed SUMMARY.md skipped gracefully', () => {
  // Write both valid and malformed files to same phase dir
  fs.writeFileSync(path.join(phaseDir, '01-01-SUMMARY.md'), validContent);
  fs.writeFileSync(path.join(phaseDir, '01-02-SUMMARY.md'), noFrontmatterContent);
  fs.writeFileSync(path.join(phaseDir, '01-03-SUMMARY.md'), brokenYamlContent);

  const result = runGsdTools('history-digest', tmpDir);
  assert.ok(result.success, `Command should succeed despite malformed files: ${result.error}`);
  // Assert valid file still parsed
  assert.ok(digest.phases['01'].provides.includes('Valid feature'));
});
```

**Numeric sort verification:**
```javascript
assert.deepStrictEqual(
  output.directories,
  ['01-foundation', '02-api', '10-final'],
  'should be sorted numerically'
);
```

## Missing Test Coverage

**ui-ux-pro-max-skill/cli:**
- Zero tests exist for the TypeScript CLI (`cli/src/`)
- No tests for: `initCommand`, `detectAIType`, `generatePlatformFiles`, `renderSkillFile`, `copyFolders`, `loadPlatformConfig`
- No test runner configured in `cli/package.json`

**app.py (Streamlit):**
- No tests exist for the Python investment dashboard
- No test runner configured

**get-shit-done hooks:**
- `gsd-statusline.js` and `gsd-check-update.js` have no tests
- `bin/install.js` (1800+ lines) has no tests

---

*Testing analysis: 2026-02-18*
