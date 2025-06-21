import * as tokens from '../../theme/generated';

describe('Design token build', () => {
  it('should export at least one token value', () => {
    // We expect ColorBrandPrimary to be defined and match the JSON source
    expect(tokens.ColorBrandPrimary).toBe('#4fd1c7');
  });
}); 