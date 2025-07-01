# Pull Request

## Description

<!-- Provide a brief summary of the changes made in this PR -->

## Related Issues/Tasks

<!-- Link to relevant GitHub issues -->

- Closes #<!-- issue number -->
- Related to #<!-- issue number -->

## Type of Change

Please check the type of change your PR introduces:

- [ ] 🐛 **Bug fix** (non-breaking change which fixes an issue)
- [ ] ✨ **New feature** (non-breaking change which adds functionality)
- [ ] 💥 **Breaking change** (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 **Documentation** (documentation only changes)
- [ ] 🧹 **Chore** (maintenance, dependencies, or tooling changes)
- [ ] ♻️ **Refactor** (code change that neither fixes a bug nor adds a feature)
- [ ] ⚡ **Performance** (code change that improves performance)
- [ ] 🔒 **Security** (security-related changes)

## Checklist

### Code Quality

- [ ] PR title follows commit message guidelines
- [ ] All code is formatted with Black and isort
- [ ] Code passes flake8 linting
- [ ] No sensitive data, API keys, or secrets are included
- [ ] Pre-commit hooks pass successfully

### Testing

- [ ] Tests are added/updated for new functionality
- [ ] All existing tests pass
- [ ] Backend coverage meets 90% threshold (if backend changes)
- [ ] Frontend coverage meets 75% threshold (if frontend changes)
- [ ] Security tests pass (if applicable)
- [ ] Property-based tests updated (if applicable)
- [ ] Performance tests considered and added (if applicable)

### Documentation & Review

- [ ] Documentation is updated as needed
- [ ] API documentation updated (if API changes)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Linked to relevant issues
- [ ] Screenshots/demos included (for UI changes)

### Dependencies & Infrastructure

- [ ] New dependencies are justified and secure
- [ ] Database migrations tested (if applicable)
- [ ] Environment variables documented (if new ones added)

## Testing Instructions

<!-- Describe the steps to test your changes -->

### Prerequisites

<!-- List any setup requirements -->

### Manual Testing Steps

1. <!-- Step 1 -->
2. <!-- Step 2 -->
3. <!-- Step 3 -->

### Automated Testing

<!-- Describe any specific test commands or scenarios -->

```bash
# Backend tests
cd backend && pytest -m "not nightly"

# Frontend tests
cd frontend && npm test

# Security tests (if applicable)
cd backend && pytest -m security

# Performance tests (if applicable)
cd backend && pytest -m performance
```

## Additional Context

<!-- Any extra information, notes, or context for reviewers -->

### Screenshots/Demos

<!-- Include screenshots, GIFs, or video demos for UI changes -->

### Breaking Changes

<!-- If this is a breaking change, describe the impact and migration path -->

### Performance Impact

<!-- Describe any performance implications -->

### Security Considerations

<!-- Highlight any security-related changes or considerations -->

---

**Reviewer Guidelines:**

- Verify all checklist items are completed
- Test the changes locally following the testing instructions
- Check code quality, security, and performance implications
- Ensure documentation is updated appropriately
