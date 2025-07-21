# FRONTEND_WORKFLOW.md

> **Audience**: Claude Code when working on React/TypeScript frontend code
> **Scope**: All tasks involving `frontend/` directory, React components, TypeScript files, styles

---

## Essential Setup

### 1. Navigate to Frontend Directory

**ALWAYS run this first** before any frontend task:

```bash
cd frontend
```

### 2. Verify Environment

```bash
node --version   # Check Node.js version
npm --version    # Check npm version
npm list --depth=0  # Check installed packages
```

---

## Testing Workflow

### Primary Test Commands

```bash
npm run test           # Vitest unit tests (default)
npm run cypress:run    # E2E tests (headless)
```

### Development Testing

```bash
npm run test:watch     # Watch mode for unit tests
npm run cypress:open   # Interactive E2E testing
```

### Single Test Debugging

When working on specific failing tests:

```bash
# Specific test file
npm run test -- path/to/component.test.tsx

# Test pattern matching
npm run test -- --grep "user login"

# Watch specific file
npm run test -- --watch path/to/component.test.tsx
```

### Coverage Reports

```bash
npm run test:coverage  # Generate test coverage report
```

---

## Code Quality & Linting

### Before Every Commit

```bash
npm run lint           # ESLint checking
npm run format         # Prettier formatting
npm run type-check     # TypeScript type checking
```

### Individual Commands

```bash
npm run lint:fix       # Auto-fix ESLint issues
npm run prettier       # Format with Prettier
npm run tsc            # TypeScript compiler check
```

---

## Development Server

### Start Development Server

```bash
npm run dev            # Start Vite development server
npm run preview        # Preview production build
```

### Build Commands

```bash
npm run build          # Production build
npm run build:analyze  # Build with bundle analyzer
```

---

## Common Frontend Tasks

### Component Development

1. **Create component**: Follow naming conventions (`PascalCase.tsx`)
2. **Test first**: Write test file alongside component
3. **Implement**: Code the component with TypeScript
4. **Style**: Use Tailwind CSS classes
5. **Validate**: Run `npm run test` and fix any failures
6. **Type check**: Ensure `npm run type-check` passes

### State Management

1. **Local state**: Use `useState`, `useReducer` for component state
2. **Global state**: Follow established patterns (Context, Zustand, etc.)
3. **Server state**: Use appropriate data fetching patterns
4. **Test**: Mock external dependencies in tests

### Styling & UI

1. **Tailwind first**: Use utility classes for styling
2. **Custom CSS**: Only when Tailwind insufficient
3. **Responsive**: Mobile-first approach
4. **Accessibility**: Ensure proper ARIA attributes and keyboard navigation

---

## Testing Patterns

### Unit Tests (Vitest)

```bash
# Run all unit tests
npm run test

# Test specific component
npm run test -- src/components/Button.test.tsx

# Watch mode for TDD
npm run test:watch
```

### E2E Tests (Cypress)

```bash
# Run all E2E tests (headless)
npm run cypress:run

# Open Cypress Test Runner
npm run cypress:open

# Run specific E2E test
npm run cypress:run -- --spec "cypress/e2e/auth.cy.ts"
```

---

## Debugging Patterns

### Failed Unit Tests

```bash
# Run with verbose output
npm run test -- --reporter=verbose

# Debug specific test
npm run test -- --inspect-brk path/to/test.test.tsx
```

### Component Issues

```bash
# Start dev server and inspect in browser
npm run dev

# Check TypeScript errors
npm run type-check
```

### Build Issues

```bash
# Check for build errors
npm run build

# Analyze bundle size
npm run build:analyze
```

---

## Package Management

### Installing Dependencies

```bash
npm install <package>              # Production dependency
npm install --save-dev <package>   # Development dependency
npm update                         # Update all packages
npm audit                          # Security audit
npm audit fix                      # Fix security issues
```

### Common Development Commands

```bash
npm run storybook      # Start Storybook (if configured)
npm run test:e2e       # Alternative E2E command
npm run clean          # Clean build artifacts
```

---

## Available NPM Scripts Reference

| Purpose                | Command                 |
| ---------------------- | ----------------------- |
| **Development server** | `npm run dev`           |
| **Unit tests**         | `npm run test`          |
| **E2E tests**          | `npm run cypress:run`   |
| **Watch tests**        | `npm run test:watch`    |
| **Lint code**          | `npm run lint`          |
| **Format code**        | `npm run format`        |
| **Type checking**      | `npm run type-check`    |
| **Build production**   | `npm run build`         |
| **Preview build**      | `npm run preview`       |
| **Test coverage**      | `npm run test:coverage` |

---

## Completion Checklist

Before marking any frontend task complete:

- [ ] Working from `frontend/` directory
- [ ] All unit tests passing: `npm run test`
- [ ] E2E tests passing: `npm run cypress:run`
- [ ] TypeScript compiles: `npm run type-check`
- [ ] Linting passes: `npm run lint`
- [ ] Code properly formatted: `npm run format`
- [ ] Changes committed with conventional commit message
- [ ] Task Master updated: mark task as done
- [ ] Memory Bank updated: - Archive created: .taskmaster/memory-bank/archive/archive-<task-id>.md - Reflection created: .taskmaster/memory-bank/reflection/reflection-<task-id>.md - Progress & activeContext updated

```bash
.taskmaster/integration/scripts/complete-task.sh <task-id> "<task-title>" [context]
```

---

## Code Style Preferences

### TypeScript

- Use explicit types over `any`
- Prefer interfaces for object shapes
- Use functional components with hooks
- Keep components under 200 lines

### React Patterns

- Functional components with hooks
- Custom hooks for reusable logic
- Props interface definitions
- Proper error boundaries

### Styling

- Tailwind utility classes preferred
- Custom CSS only when necessary
- Mobile-first responsive design
- Consistent spacing using Tailwind scale

---

_Frontend workflow - Last updated: 20 July 2025_
