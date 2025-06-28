module.exports = {
  source: ['../design/design-tokens.json'],
  platforms: {
    ts: {
      transformGroup: 'js',
      buildPath: 'src/theme/generated/',
      files: [
        {
          destination: 'index.ts',
          format: 'javascript/es6',
        },
      ],
    },
  },
};
