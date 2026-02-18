# Coding Conventions

**Analysis Date:** 2026-02-18

## Naming Patterns

**Files:**
- TypeScript source files: `camelCase.ts` (e.g., `extract.ts`, `detect.ts`, `logger.ts`)
- Command files: `camelCase.ts` under `commands/` (e.g., `init.ts`, `versions.ts`, `update.ts`)
- Type definition files: `index.ts` as barrel exports
- CommonJS scripts in get-shit-done: `camelCase.cjs` (e.g., `gsd-tools.cjs`, `gsd-statusline.js`)
- Test files: `<name>.test.cjs` co-located with implementation

**Functions:**
- camelCase for all functions: `detectAIType`, `copyFolders`, `generatePlatformFiles`, `loadPlatformConfig`
- Async functions use `async`/`await` consistently, not callbacks (TypeScript layer)
- CJS layer (hooks, install scripts) uses callbacks via `readline.createInterface` when interactive

**Variables:**
- camelCase: `aiType`, `copiedFolders`, `targetDir`, `pathPrefix`
- Constants: SCREAMING_SNAKE_CASE for module-level: `AI_TYPES`, `AI_FOLDERS`, `ASSETS_DIR`, `EXCLUDED_FILES`
- Color ANSI escape strings: lowercase `const cyan`, `const green`, `const yellow`, `const reset`

**Types/Interfaces:**
- PascalCase: `AIType`, `InstallType`, `Release`, `Asset`, `InstallConfig`, `PlatformConfig`
- Interfaces prefixed by role: `DetectionResult`, `InitOptions`
- Types exported from `src/types/index.ts` as the single source of truth

## Code Style

**Formatting:**
- No automated formatter config detected (no `.prettierrc`, `.eslintrc`, or `biome.json`)
- 2-space indentation throughout (observed in all .ts and .js files)
- Single quotes in JavaScript/CommonJS; mixed single/double quotes in TypeScript (template literals common)
- Trailing newline on all source files

**Linting:**
- No ESLint or Prettier configuration detected
- TypeScript: `strict: true` enforced in `ui-ux-pro-max-skill/cli/tsconfig.json`
- TypeScript target: ES2022, module: ESNext, moduleResolution: bundler

**Python (app.py):**
- snake_case for functions: `get_portfolio_performance`
- Docstrings for functions: `"""Calculates Market Value, P&L, Allocation, and Sector"""`
- Inline comments with `# --- SECTION TITLE ---` style section headers
- `@st.cache_data(ttl=300)` decorator pattern for Streamlit caching

## Import Organization

**TypeScript order (ui-ux-pro-max-skill/cli/src):**
1. Node built-in modules with `node:` prefix: `import { readFile } from 'node:fs/promises'`
2. Third-party packages: `import chalk from 'chalk'`
3. Local types (type-only): `import type { AIType } from '../types/index.js'`
4. Local values: `import { AI_TYPES } from '../types/index.js'`
5. Local utilities/commands: `import { detectAIType } from '../utils/detect.js'`

**Import rules:**
- Always use `.js` extension for local imports (ESM with bundler resolution)
- Type-only imports use `import type { ... }` keyword
- Node built-ins always use `node:` prefix (e.g., `node:fs`, `node:path`, `node:os`)

**CommonJS (hooks, install scripts):**
- `require()` with no prefix (e.g., `require('fs')`, `require('path')`)
- No import organization enforced; utilities declared at top of file

## Error Handling

**TypeScript layer:**
- Custom error classes for distinct failure modes: `GitHubRateLimitError`, `GitHubDownloadError`
- `instanceof` checks for typed error handling: `if (error instanceof GitHubRateLimitError)`
- Graceful fallback: GitHub download fails → bundled assets fallback
- Catch blocks with empty body when errors can be safely swallowed (copy failures fall through to shell fallback)
- `process.exit(1)` on unrecoverable errors

**CommonJS layer (install scripts, hooks):**
- Silent fail with empty `catch (e) {}` for non-critical operations (file read, JSON parse)
- User-visible errors use `console.error()` with ANSI color codes
- Unexpected/unrecoverable errors propagate or call `process.exit(1)`

**Python layer (app.py):**
- `try/except Exception as e` with `st.error()` for user-visible failures
- `st.stop()` to halt execution on critical errors (e.g., database connection failure)
- Bare `except:` used in some fetch paths to silently swallow errors

## Logging

**TypeScript (ui-ux-pro-max-skill/cli):**
- Centralized logger at `cli/src/utils/logger.ts`
- Pattern: `logger.info()`, `logger.success()`, `logger.warn()`, `logger.error()`, `logger.title()`, `logger.dim()`
- Uses `chalk` for color: blue=info, green=success, yellow=warn, red=error, cyan bold=title
- Spinner (ora) for async operations: `spinner.text = '...'` during progress, `spinner.succeed()` / `spinner.fail()` / `spinner.warn()` on completion

**CommonJS hooks/installer:**
- Direct `console.log()` with ANSI escape codes (no logging abstraction)
- Color constants defined at file top: `const cyan`, `const green`, `const yellow`, `const dim`, `const reset`
- Format: `console.log(\`  ${green}✓${reset} Description\`)` for success items
- Silent output when called by hook system (no stdout noise for background tasks)

## Comments

**When to Comment:**
- JSDoc on all exported functions: `/** Description @param ... @returns ... */`
- Inline `//` for non-obvious logic, path resolution, platform compatibility notes
- Section separators: `// ──────────────────────────────` for major logical blocks
- `// Legacy`, `// TODO`, or `// Removed in vX.Y.Z` for migration/deprecation notes

**JSDoc/TSDoc:**
- All exported TypeScript functions have JSDoc blocks
- Parameter types documented in JSDoc even though TypeScript already types them
- Return types documented when non-obvious

## Function Design

**Size:** Functions are single-responsibility; large operations broken into helpers (e.g., `install()` delegates to `saveLocalPatches()`, `cleanupOrphanedFiles()`, `copyWithPathReplacement()`)

**Parameters:**
- Options passed as interface objects for 3+ params: `InitOptions`, `InstallConfig`
- Simple operations use positional params (max 3)

**Return Values:**
- Async functions return `Promise<T>` with explicit types
- Functions that may fail return `null` or empty arrays rather than throwing (e.g., `tryGitHubInstall` returns `string[] | null`)
- Consistent: file list operations return `string[]`

## Module Design

**Exports:**
- TypeScript modules: named exports only (no default exports in utility files)
- Entry point `index.ts` uses Commander pattern, no re-exports
- Types centralized in `src/types/index.ts` barrel file

**Barrel Files:**
- `src/types/index.ts` serves as the type barrel: exports all types and constants
- No barrel files for utilities; each utility imported directly by path

---

*Convention analysis: 2026-02-18*
