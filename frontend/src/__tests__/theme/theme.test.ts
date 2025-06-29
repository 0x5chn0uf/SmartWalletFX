import { createAppTheme } from '../../theme';
import * as tokens from '../../theme/generated';

describe('createAppTheme', () => {
  it('should map ColorBrandPrimary token to theme palette.primary.main', () => {
    const theme = createAppTheme();
    expect(theme.palette.primary.main).toBe(tokens.ColorBrandPrimary);
  });
});
