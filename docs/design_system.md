# Design System – Token Build Pipeline

> **Status**: Initial version – covers token build pipeline introduced in Sub-task 70.2 (2025-06-21).

This document explains how the cross-platform **design tokens** defined in `design/design-tokens.json` are transformed into TypeScript constants that power the MUI theme.  It covers the file layout, build commands, CI integration, and contribution workflow.

---

## 1. Source of Truth – `design/design-tokens.json`

* Located at the repository root under `design/`.
* Follows the [W3C Design Tokens](https://design-tokens.github.io/community-group/format/) draft specification: each **leaf‐level token** is an object with a `value` property.
  ```json
  "color": {
    "brand": {
      "primary": { "value": "#4fd1c7" }
    }
  }
  ```
* **Do not** add framework-specific values here (e.g. CSS variables, `px` suffixes). Keep it raw.

### Adding / Updating Tokens
1. Edit `design/design-tokens.json`.  
2. Ensure every new leaf has a `value` property.  
3. Run `make build-tokens` (or `npm run build:tokens` inside `frontend/`) to regenerate the TypeScript module.  
4. Commit **both** the JSON edit **and** the generated file.

---

## 2. Build Tool – Style Dictionary

We use [`style-dictionary`](https://amzn.github.io/style-dictionary/#/) (v5) to convert design tokens into code assets.

* **Config file**: `frontend/sd.config.js`
* **Build path**: `frontend/src/theme/generated/index.ts`
* **Transform group**: `javascript/es6` (suitable for TypeScript import).

### Local Commands
```
# Root level (delegates to frontend)
make build-tokens     # preferred alias

# Directly in frontend
cd frontend
npm run build:tokens   # runs Style Dictionary build
```

The output file will contain ES module exports such as:
```ts
export const ColorBrandPrimary = "#4fd1c7";
export const FontSizeBody = 16;
```

---

## 3. Continuous Integration

The **CI/CD pipeline** (see `.github/workflows/ci-cd.yml`) includes a dedicated step in the `build-frontend` job:
```yaml
- name: Generate design tokens
  working-directory: ./frontend
  run: npm run build:tokens --if-present
```
This guarantees that the generated file is always refreshed in pull-requests and production builds.  

**Fail-fast**: If the generated file is missing or stale, TypeScript imports will fail and the build will error.

---

## 4. Unit Test Guard

A Jest unit test (`frontend/src/__tests__/unit/tokens.build.test.ts`) asserts that at least one known token (e.g. `ColorBrandPrimary`) is exported.  This protects against accidental mis-configuration or broken builds.

---

## 5. Contributing Workflow

1. Modify or add tokens in `design/design-tokens.json`.
2. Run `make build-tokens` – commit updated JSON **and** generated TS file.
3. Run `npm test` (frontend) to ensure the token test still passes.
4. Open PR – CI will re-generate tokens and double-check.

> **Tip**: Use [`docs/security_testing.md`](security_testing.md) helpers to add WCAG contrast tests for new colour pairs.

---

## 6. Roadmap

| Milestone | Description |
|-----------|-------------|
| 70.3 | Integrate token linting (WCAG contrast) into CI |
| 70.4 | Add Storybook theme switcher (light / dark) using generated tokens |
| 70.5 | Publish design token documentation site via Storybook Docs |

---

_Last updated: 2025-06-21_ 