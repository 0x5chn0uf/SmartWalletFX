/* eslint-disable prettier/prettier */
import { createTheme, Theme } from '@mui/material/styles';
import * as tokens from './generated';

/**
 * createAppTheme
 * Builds a Material-UI theme from the auto-generated design tokens.
 * Supports light and dark modes – default is dark.
 */
export const createAppTheme = (mode: 'light' | 'dark' = 'dark'): Theme => {
  const isDark = mode === 'dark';

  return createTheme({
    palette: {
      mode,
      primary: {
        main: tokens.ColorBrandPrimary,
        contrastText: tokens.ColorTextPrimary,
      },
      secondary: {
        main: tokens.ColorBrandSecondary,
        contrastText: tokens.ColorTextPrimary,
      },
      background: {
        default: isDark ? tokens.ColorBackgroundDefault : '#ffffff',
        paper: isDark ? tokens.ColorBackgroundSurface : '#fafafa',
      },
      text: {
        primary: isDark ? tokens.ColorTextPrimary : tokens.ColorTextInverse,
        secondary: tokens.ColorTextSecondary,
      },
    },
    typography: {
      fontFamily: tokens.FontFamilyPrimary,
      h1: {
        fontSize: tokens.FontSizeH1,
        fontWeight: tokens.FontWeightBold,
        lineHeight: tokens.FontLineheightHeading,
      },
      h2: {
        fontSize: tokens.FontSizeH2,
        fontWeight: tokens.FontWeightSemibold,
        lineHeight: tokens.FontLineheightHeading,
      },
      body1: {
        fontSize: tokens.FontSizeBody,
        fontWeight: tokens.FontWeightRegular,
        lineHeight: tokens.FontLineheightBody,
      },
      caption: {
        fontSize: tokens.FontSizeCaption,
        fontWeight: tokens.FontWeightRegular,
        lineHeight: tokens.FontLineheightBody,
      },
    },
    shape: {
      borderRadius: tokens.SizeRadiiMd,
    },
    // Use the xs spacing value (4px) as base multiplier for MUI spacing helper
    spacing: tokens.SizeSpacingXs,
    // Provide a minimal shadows array derived from elevation tokens
    shadows: [
      'none',
      tokens.Elevation1,
      tokens.Elevation2,
      tokens.Elevation3,
      tokens.Elevation4,
      tokens.Elevation5,
      ...Array(19).fill(tokens.Elevation5),
    ] as unknown as Theme['shadows'],
  });
};
