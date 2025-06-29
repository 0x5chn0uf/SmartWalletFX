# Accessibility Standards & Guidelines

This document outlines the accessibility standards, tools, and development workflow for the trading bot application.

## WCAG Compliance Standards

We maintain **WCAG 2.1 AA** compliance across all user interfaces. This means:

### Color Contrast Requirements

- **Normal text**: Minimum 4.5:1 contrast ratio
- **Large text (18pt+ or 14pt+ bold)**: Minimum 3:1 contrast ratio
- **Muted/decorative text**: Minimum 2.5:1 contrast ratio
- **UI components and graphics**: Minimum 3:1 contrast ratio

### Text & Typography

- **Font sizes**: Minimum 16px for body text
- **Line spacing**: At least 1.5x line height
- **Text resizing**: Support up to 200% zoom without horizontal scrolling

### Keyboard Navigation

- **Tab order**: Logical, intuitive tab sequence
- **Focus indicators**: Visible focus states for all interactive elements
- **Skip links**: Skip to main content links where appropriate
- **Keyboard shortcuts**: No keyboard traps

### Screen Reader Support

- **Semantic HTML**: Proper heading hierarchy (h1-h6)
- **ARIA labels**: Descriptive labels for interactive elements
- **Alt text**: Meaningful alternative text for images
- **Landmarks**: Proper use of ARIA landmarks

## Automated Testing Tools

### Design Token Validation

```bash
# Validate all color combinations meet WCAG AA
python scripts/contrast_check.py --strict

# Detailed validation with verbose output
python scripts/contrast_check.py --verbose
```

### Frontend Unit Tests

```bash
# Run accessibility tests for design tokens
npm test -- --testPathPattern="accessibility"

# Run all tests including accessibility
npm test -- --watchAll=false --ci
```

### Storybook Accessibility Testing

```bash
# Run Storybook with accessibility addon
npm run storybook

# Run automated accessibility tests on stories
npm run a11y:test
```

## Development Workflow

### 1. Design Token Validation

All color combinations in `design/design-tokens.json` are automatically validated:

- **Text colors** vs **background colors** combinations
- **Muted text** uses relaxed 2.5:1 threshold
- **Inverse text** combinations are filtered for realistic usage
- **CI integration** fails builds on violations

### 2. Component Development

When creating new components:

1. **Use design tokens** from the generated theme
2. **Test in Storybook** with accessibility addon enabled
3. **Verify keyboard navigation** works correctly
4. **Add ARIA attributes** where needed
5. **Test with screen readers** (NVDA, JAWS, VoiceOver)

### 3. Code Review Checklist

- [ ] Color contrast meets WCAG AA standards
- [ ] Keyboard navigation works correctly
- [ ] Screen reader announcements are appropriate
- [ ] Focus indicators are visible
- [ ] Semantic HTML structure is used
- [ ] ARIA attributes are correctly implemented

## Common Accessibility Patterns

### Button Components

```tsx
// Good: Proper ARIA and keyboard support
<Button
  aria-label="Close dialog"
  onClick={handleClose}
  onKeyDown={(e) => e.key === "Escape" && handleClose()}
>
  Close
</Button>
```

### Form Controls

```tsx
// Good: Proper labeling and error handling
<TextField
  label="Email Address"
  aria-describedby="email-error"
  error={!!emailError}
  helperText={emailError}
  id="email-error"
/>
```

### Navigation

```tsx
// Good: Skip link for keyboard users
<a href="#main-content" className="skip-link">
  Skip to main content
</a>
```

## Testing with Assistive Technologies

### Screen Readers

- **Windows**: NVDA (free) or JAWS
- **macOS**: VoiceOver (built-in)
- **Linux**: Orca (free)

### Keyboard Testing

- Navigate using Tab, Shift+Tab, Enter, Space, Arrow keys
- Verify focus indicators are visible
- Test all interactive elements

### Color Contrast Tools

- **Browser DevTools**: Chrome/Firefox accessibility panels
- **axe DevTools**: Browser extension for automated testing
- **Contrast Checker**: Online tools for manual verification

## CI/CD Integration

Accessibility checks are integrated into the CI pipeline:

1. **Design token validation** runs on every build
2. **Frontend accessibility tests** are part of the test suite
3. **Build fails** if accessibility violations are detected
4. **Reports** are generated for review

## Resources & References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Color Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [axe-core Documentation](https://github.com/dequelabs/axe-core)

## Getting Help

For accessibility questions or issues:

1. **Check this documentation** first
2. **Review WCAG guidelines** for specific requirements
3. **Test with assistive technologies** to understand user experience
4. **Consult the team** for complex accessibility challenges

## Continuous Improvement

We regularly:

- **Audit existing components** for accessibility compliance
- **Update tools and dependencies** to latest versions
- **Train team members** on accessibility best practices
- **Gather user feedback** from users with disabilities
