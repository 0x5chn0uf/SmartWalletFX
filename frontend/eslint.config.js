/* eslint-env node */
const { FlatCompat } = require('@eslint/eslintrc');
const js = require('@eslint/js');
const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
});

module.exports = [
  // globs to ignore
  {
    ignores: ['node_modules/**', 'build/**', 'dist/**', 'coverage/**'],
  },
  // bring in the shareable configs we used to extend in .eslintrc.json
  ...compat.config({
    extends: [
      'eslint:recommended',
      'plugin:@typescript-eslint/recommended',
      'plugin:react/recommended',
      'plugin:react-hooks/recommended',
    ],
    parserOptions: {
      ecmaVersion: 2021,
      sourceType: 'module',
      ecmaFeatures: { jsx: true },
    },
    settings: {
      react: { version: 'detect' },
    },
    env: {
      browser: true,
      es2021: true,
      node: true,
      jest: true,
    },
  }),
  // project-specific rule tweaks & overrides
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    rules: {
      'react/react-in-jsx-scope': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      '@typescript-eslint/no-require-imports': 'off',
    },
  },
  {
    files: ['**/__tests__/**', '**/*.test.*', 'cypress/**', 'scripts/**'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
      '@typescript-eslint/no-require-imports': 'off',
    },
  },
];
