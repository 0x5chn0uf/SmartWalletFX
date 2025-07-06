import { createTheme, Theme } from '@mui/material/styles';
import * as tokens from './generated';

/**
 * createAppTheme
 * Builds a Material-UI theme from the auto-generated design tokens.
 */
export const createAppTheme = (): Theme => {
  return createTheme({
    palette: {
      mode: 'dark',
      primary: {
        main: tokens.ColorBrandPrimary,
        contrastText: tokens.ColorTextPrimary,
      },
      secondary: {
        main: tokens.ColorBrandSecondary,
        contrastText: tokens.ColorTextPrimary,
      },
      background: {
        default: tokens.ColorBackgroundDefault,
        paper: tokens.ColorBackgroundSurface,
      },
      text: {
        primary: tokens.ColorTextPrimary,
        secondary: tokens.ColorTextSecondary,
      },
    },
    typography: {
      fontFamily: tokens.FontFamilyPrimary,
      h1: {
        fontSize: '56px',
        fontWeight: tokens.FontWeightBold,
        lineHeight: 1.05,
      },
      h2: {
        fontSize: tokens.FontSizeH2,
        fontWeight: tokens.FontWeightSemibold,
        lineHeight: tokens.FontLineheightHeading,
      },
      body1: {
        fontSize: '18px',
        fontWeight: tokens.FontWeightRegular,
        lineHeight: tokens.FontLineheightBody,
      },
      button: {
        fontWeight: tokens.FontWeightMedium,
        letterSpacing: '0.2px',
        textTransform: 'none',
      },
      caption: {
        fontSize: tokens.FontSizeCaption,
        fontWeight: tokens.FontWeightRegular,
        lineHeight: tokens.FontLineheightBody,
      },
    },
    shape: {
      borderRadius: parseInt(tokens.SizeRadiiMd.toString(), 10),
    },
    spacing: 8,
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
