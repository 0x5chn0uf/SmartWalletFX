import React from 'react';
import { Button as MuiButton, ButtonProps as MuiButtonProps } from '@mui/material';
import { styled } from '@mui/material/styles';
import * as tokens from '../../../theme/generated';

export interface ButtonProps extends Omit<MuiButtonProps, 'variant'> {
  variant?: 'primary' | 'secondary' | 'text';
  size?: 'small' | 'medium' | 'large';
}

const StyledButton = styled(MuiButton)<{
  customVariant?: 'primary' | 'secondary' | 'text';
  customSize?: 'small' | 'medium' | 'large';
}>(({ theme, customVariant = 'primary', customSize = 'medium' }) => {
  const getVariantStyles = () => {
    switch (customVariant) {
      case 'primary':
        return {
          backgroundColor: tokens.ColorBrandPrimary,
          color: tokens.ColorTextInverse,
          '&:hover': {
            backgroundColor: theme.palette.primary.dark,
          },
        };
      case 'secondary':
        return {
          backgroundColor: tokens.ColorBrandSecondary,
          color: tokens.ColorTextPrimary,
          '&:hover': {
            backgroundColor: theme.palette.secondary.dark,
          },
        };
      case 'text':
        return {
          backgroundColor: 'transparent',
          color: tokens.ColorBrandPrimary,
          '&:hover': {
            backgroundColor: theme.palette.action.hover,
          },
        };
      default:
        return {};
    }
  };

  const getSizeStyles = () => {
    switch (customSize) {
      case 'small':
        return {
          padding: `${tokens.SizeSpacingXs}px ${tokens.SizeSpacingSm}px`,
          fontSize: tokens.FontSizeSmall,
          borderRadius: tokens.SizeRadiiSm,
        };
      case 'large':
        return {
          padding: `${tokens.SizeSpacingMd}px ${tokens.SizeSpacingLg}px`,
          fontSize: tokens.FontSizeBody,
          borderRadius: tokens.SizeRadiiLg,
        };
      default: // medium
        return {
          padding: `${tokens.SizeSpacingSm}px ${tokens.SizeSpacingMd}px`,
          fontSize: tokens.FontSizeBody,
          borderRadius: tokens.SizeRadiiMd,
        };
    }
  };

  return {
    fontFamily: tokens.FontFamilyPrimary,
    fontWeight: tokens.FontWeightMedium,
    textTransform: 'none' as const,
    boxShadow: tokens.Elevation1,
    transition: 'all 0.2s ease-in-out',
    ...getVariantStyles(),
    ...getSizeStyles(),
    '&:disabled': {
      opacity: 0.6,
      cursor: 'not-allowed',
    },
  };
});

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  ...props
}) => {
  // Map our custom variants to MUI variants
  const muiVariant: 'text' | 'contained' = variant === 'text' ? 'text' : 'contained';

  return (
    <StyledButton variant={muiVariant} customVariant={variant} customSize={size} {...props}>
      {children}
    </StyledButton>
  );
};

export default Button;
