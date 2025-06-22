import React from 'react';
import { Typography as MuiTypography, TypographyProps as MuiTypographyProps } from '@mui/material';
import { styled } from '@mui/material/styles';
import * as tokens from '../../../theme/generated';

export interface TypographyProps extends Omit<MuiTypographyProps, 'variant'> {
  variant?: 'display' | 'h1' | 'h2' | 'body' | 'caption' | 'small';
  weight?: 'regular' | 'medium' | 'semibold' | 'bold';
}

const StyledTypography = styled(MuiTypography)<{
  customVariant?: 'display' | 'h1' | 'h2' | 'body' | 'caption' | 'small';
  customWeight?: 'regular' | 'medium' | 'semibold' | 'bold';
}>(({ customVariant = 'body', customWeight = 'regular' }) => {
  const getVariantStyles = () => {
    switch (customVariant) {
      case 'display':
        return {
          fontSize: tokens.FontSizeDisplay,
          lineHeight: tokens.FontLineheightDisplay,
          fontWeight: tokens.FontWeightBold,
        };
      case 'h1':
        return {
          fontSize: tokens.FontSizeH1,
          lineHeight: tokens.FontLineheightHeading,
          fontWeight: tokens.FontWeightBold,
        };
      case 'h2':
        return {
          fontSize: tokens.FontSizeH2,
          lineHeight: tokens.FontLineheightHeading,
          fontWeight: tokens.FontWeightSemibold,
        };
      case 'caption':
        return {
          fontSize: tokens.FontSizeCaption,
          lineHeight: tokens.FontLineheightBody,
          fontWeight: tokens.FontWeightRegular,
        };
      case 'small':
        return {
          fontSize: tokens.FontSizeSmall,
          lineHeight: tokens.FontLineheightBody,
          fontWeight: tokens.FontWeightRegular,
        };
      default: // body
        return {
          fontSize: tokens.FontSizeBody,
          lineHeight: tokens.FontLineheightBody,
          fontWeight: tokens.FontWeightRegular,
        };
    }
  };

  const getWeightStyles = () => {
    switch (customWeight) {
      case 'medium':
        return { fontWeight: tokens.FontWeightMedium };
      case 'semibold':
        return { fontWeight: tokens.FontWeightSemibold };
      case 'bold':
        return { fontWeight: tokens.FontWeightBold };
      default: // regular
        return { fontWeight: tokens.FontWeightRegular };
    }
  };

  return {
    fontFamily: tokens.FontFamilyPrimary,
    color: tokens.ColorTextPrimary,
    margin: 0,
    ...getVariantStyles(),
    ...getWeightStyles(),
  };
});

export const Typography: React.FC<TypographyProps> = ({
  children,
  variant = 'body',
  weight = 'regular',
  ...props
}) => {
  // Map our custom variants to MUI variants for semantic HTML
  const getMuiVariant = (customVariant: string): MuiTypographyProps['variant'] => {
    switch (customVariant) {
      case 'display':
      case 'h1':
        return 'h1';
      case 'h2':
        return 'h2';
      case 'body':
        return 'body1';
      case 'caption':
        return 'caption';
      case 'small':
        return 'body2';
      default:
        return 'body1';
    }
  };

  return (
    <StyledTypography
      variant={getMuiVariant(variant)}
      customVariant={variant}
      customWeight={weight}
      {...props}
    >
      {children}
    </StyledTypography>
  );
};

export default Typography;
