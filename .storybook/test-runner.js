const { getStoryContext } = require('@storybook/test-runner');
const AxeBuilder = require('axe-core').AxeBuilder;

module.exports = {
  async preRender(page, context) {
    // Nothing to do before render
  },

  async postRender(page, context) {
    const storyContext = await getStoryContext(page, context);

    // Only run axe on docs stories that opt-in via parameters or all by default
    const runAxe = storyContext?.parameters?.a11y?.disable !== true;
    if (!runAxe) {
      return;
    }

    const results = await new AxeBuilder({ page })
      .disableRules(['color-contrast']) // keep contrast handled in separate test
      .analyze();

    if (results.violations.length > 0) {
      const formatted = results.violations
        .map((v) => `${v.help} (${v.id})\n  Affected: ${v.nodes.length}`)
        .join('\n');
      throw new Error(`A11y Violations in story ${context.id}:\n${formatted}`);
    }
  },
}; 