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

## 6. MUI Theme Integration

> **Status**: Implemented in Sub-task 70.3 (2025-06-22).

This section details how the generated tokens are used to create a dynamic, mode-aware MUI theme.

### `ThemeProvider`
- **Location**: `frontend/src/providers/ThemeProvider.tsx`
- **Function**: This React context provider is the root of the theming system. It manages the current color mode ('light' or 'dark') and makes it available to all child components.
- **Global Injection**: It is wrapped around the entire application in `src/index.js`, ensuring `CssBaseline` and the MUI theme are applied globally.

### `createAppTheme`
- **Location**: `frontend/src/theme/index.ts`
- **Function**: This function receives the current mode ('light' | 'dark') and returns a complete MUI theme object. It maps the raw values from `theme/generated/index.ts` to the structured properties of the MUI `palette`, `typography`, `shadows`, etc.

### Switching Modes
A dedicated component, `ColorModeToggle`, has been created to switch between light and dark themes.
- **Location**: `frontend/src/components/ColorModeToggle/ColorModeToggle.tsx`
- **Usage**: Simply drop this component into any part of the UI (it's currently in the main `AppBar`). It automatically consumes the `ColorModeContext` and handles the toggle logic.

### Using the Theme in Components
To access theme values in your components:
1. **`useTheme` Hook**: For logic-based styling.
   ```tsx
   import { useTheme } from '@mui/material/styles';

   const MyComponent = () => {
     const theme = useTheme();
     // ...
   };
   ```
2. **`sx` Prop**: For concise, inline styling that has access to the theme.
   ```tsx
   <Box sx={{ p: theme => theme.spacing(2), color: 'primary.main' }}>
     Hello
   </Box>
   ```

---

## 7. Roadmap
| Milestone | Description | Status |
|-----------|-------------|--------|
| 70.5 | Integrate token linting (WCAG contrast) into CI | ⏳ PENDING |
| 70.6 | Add Storybook visual regression testing (e.g., Chromatic) | ⏳ PENDING |
| 70.7 | Publish design token documentation site via Storybook Docs | ⏳ PENDING |
| 71.0 | Create shared `Layout` components (SideNav, Header, Footer) | ⏳ PENDING |


---

_Last updated: 2025-06-22_ 