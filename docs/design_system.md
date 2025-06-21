# Design System – Token Build Pipeline

> **Status**: Complete implementation – covers all subtasks 70.1-70.7 (2025-06-22).

This document explains how the cross-platform **design tokens** defined in `design/design-tokens.json` are transformed into TypeScript constants that power the MUI theme.  It covers the file layout, build commands, CI integration, contribution workflow, and governance guidelines.

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

> **Tip**: Use [`docs/accessibility.md`](accessibility.md) helpers to add WCAG contrast tests for new colour pairs.

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

## 7. Storybook Component Library

> **Status**: Implemented in Sub-task 70.4 (2025-06-22).

The design system includes a comprehensive Storybook component library that showcases all design tokens and provides interactive documentation.

### Available Components
- **Button**: Primary, secondary, and text variants with different sizes and states
- **Card**: Surface component with elevation, padding, and content areas
- **Typography**: Text components demonstrating the typography scale and weights
- **Surface**: Basic container with background colors and spacing
- **Accessibility Guide**: Interactive documentation for accessibility best practices

### Running Storybook
```bash
cd frontend
npm run storybook
```

### Component Development
When creating new components:
1. Use design tokens from `frontend/src/theme/generated/`
2. Create Storybook stories for all variants
3. Include accessibility testing with `@storybook/addon-a11y`
4. Test in both light and dark themes

---

## 8. Accessibility & Quality Assurance

> **Status**: Implemented in Sub-task 70.5 (2025-06-22).

### WCAG AA Compliance
- **Automated Testing**: All color combinations are validated against WCAG AA standards
- **CI Integration**: Accessibility checks run automatically in the build pipeline
- **Tools**: `wcag-contrast` library for accurate contrast ratio calculations
- **Documentation**: Comprehensive accessibility guide in `docs/accessibility.md`

### Testing Commands
```bash
# Run accessibility tests
npm test -- --testPathPattern="accessibility"

# Run contrast checker
python scripts/contrast_check.py --strict

# Run Storybook accessibility tests
npm run a11y:test
```

---

## 9. Governance & Token Versioning

### Token Naming Conventions
- **Semantic naming**: Use descriptive names that convey purpose (e.g., `color.text.primary` not `color.blue`)
- **Namespacing**: Group related tokens with dots (e.g., `color.brand.primary`, `spacing.component.small`)
- **Consistency**: Follow established patterns for similar token types

### Change Management
1. **Breaking Changes**: Any token removal or value changes require:
   - Design review and approval
   - Migration plan for existing components
   - Version bump in `design/design-tokens.json`
   - Documentation update

2. **Additive Changes**: New tokens require:
   - Design review
   - Accessibility validation (for colors)
   - Storybook story updates
   - Documentation update

### Version Control
- **Token Versioning**: Track major changes in `design/design-tokens.json` with version comments
- **Changelog**: Document significant changes in this file
- **Migration Guide**: Provide upgrade paths for breaking changes

### Review Process
1. **Design Review**: All token changes require design team approval
2. **Technical Review**: Implementation must follow established patterns
3. **Accessibility Review**: Color changes must pass WCAG AA validation
4. **Documentation Review**: Ensure all changes are properly documented

---

## 10. Contribution Guidelines

### For Designers
1. **Token Creation**: Work with developers to define new tokens
2. **Accessibility**: Ensure all color combinations meet WCAG AA standards
3. **Documentation**: Update design system documentation when adding new tokens
4. **Testing**: Review Storybook stories for new components

### For Developers
1. **Token Usage**: Always use design tokens instead of hardcoded values
2. **Component Development**: Create Storybook stories for all new components
3. **Testing**: Include accessibility tests for all components
4. **Documentation**: Update component documentation and examples

### For QA Engineers
1. **Accessibility Testing**: Run accessibility tests on all new components
2. **Cross-browser Testing**: Ensure components work in all supported browsers
3. **Theme Testing**: Verify components work correctly in both light and dark themes
4. **Regression Testing**: Ensure changes don't break existing components

---

## 11. Roadmap & Status

| Milestone | Description | Status | Completion Date |
|-----------|-------------|--------|-----------------|
| 70.1 | Seed Token JSON | ✅ **COMPLETED** | 2025-06-21 |
| 70.2 | Token Build Pipeline | ✅ **COMPLETED** | 2025-06-22 |
| 70.3 | MUI Theme Integration | ✅ **COMPLETED** | 2025-06-22 |
| 70.4 | Storybook Setup & Baseline Components | ✅ **COMPLETED** | 2025-06-22 |
| 70.5 | Accessibility & Contrast Automation | ✅ **COMPLETED** | 2025-06-22 |
| 70.6 | CI Visual Regression | ❌ **SKIPPED** | N/A |
| 70.7 | Documentation & Governance | ✅ **COMPLETED** | 2025-06-22 |

### Future Enhancements
- **Component Library Expansion**: Add more complex components (forms, navigation, data tables)
- **Design Token Analytics**: Track token usage across the application
- **Design System Website**: Create a public-facing design system documentation site
- **Component Testing**: Add comprehensive unit and integration tests for all components

---

## 12. Troubleshooting

### Common Issues

**Build Failures**
- Ensure `design/design-tokens.json` is valid JSON
- Run `make build-tokens` to regenerate TypeScript files
- Check that all token names follow naming conventions

**Accessibility Violations**
- Use the contrast checker: `python scripts/contrast_check.py`
- Review color combinations in `docs/accessibility.md`
- Test with screen readers and keyboard navigation

**Theme Issues**
- Verify `ThemeProvider` is wrapping the application
- Check that components use theme values instead of hardcoded styles
- Test in both light and dark modes

**Storybook Problems**
- Ensure all dependencies are installed: `npm install`
- Check Storybook configuration in `.storybook/`
- Verify components are properly exported

### Getting Help
- **Documentation**: Check this file and related documentation
- **Code Examples**: Review Storybook stories for implementation examples
- **Accessibility**: Consult `docs/accessibility.md` for guidelines
- **Issues**: Create GitHub issues for bugs or feature requests

---

_Last updated: 2025-06-22_ 