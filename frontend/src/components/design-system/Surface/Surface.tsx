import React from 'react';
import { Box, BoxProps } from '@mui/material';
import { styled } from '@mui/material/styles';
import * as tokens from '../../../theme/generated';

export interface SurfaceProps extends Omit<BoxProps, 'bgcolor'> {
  variant?: 'default' | 'surface' | 'elevated';
  padding?: 'none' | 'small' | 'medium' | 'large';
  borderRadius?: 'none' | 'small' | 'medium' | 'large';
}

const StyledSurface = styled(Box)<{
  customVariant?: 'default' | 'surface' | 'elevated';
  customPadding?: 'none' | 'small' | 'medium' | 'large';
  customBorderRadius?: 'none' | 'small' | 'medium' | 'large';
}>(({ customVariant = 'default', customPadding = 'medium', customBorderRadius = 'medium' }) => {
  const getVariantStyles = () => {
    switch (customVariant) {
      case 'surface':
        return {
          backgroundColor: tokens.ColorBackgroundSurface,
        };
      case 'elevated':
        return {
          backgroundColor: tokens.ColorBackgroundElevated,
        };
      default: // default
        return {
          backgroundColor: tokens.ColorBackgroundDefault,
        };
    }
  };

  const getPaddingStyles = () => {
    switch (customPadding) {
      case 'none':
        return {
          padding: 0,
        };
      case 'small':
        return {
          padding: tokens.SizeSpacingSm,
        };
      case 'large':
        return {
          padding: tokens.SizeSpacingLg,
        };
      default: // medium
        return {
          padding: tokens.SizeSpacingMd,
        };
    }
  };

  const getBorderRadiusStyles = () => {
    switch (customBorderRadius) {
      case 'none':
        return {
          borderRadius: 0,
        };
      case 'small':
        return {
          borderRadius: tokens.SizeRadiiSm,
        };
      case 'large':
        return {
          borderRadius: tokens.SizeRadiiLg,
        };
      default: // medium
        return {
          borderRadius: tokens.SizeRadiiMd,
        };
    }
  };

  return {
    fontFamily: tokens.FontFamilyPrimary,
    ...getVariantStyles(),
    ...getPaddingStyles(),
    ...getBorderRadiusStyles(),
  };
});

export const Surface: React.FC<SurfaceProps> = ({
  children,
  variant = 'default',
  padding = 'medium',
  borderRadius = 'medium',
  ...props
}) => {
  return (
    <StyledSurface
      customVariant={variant}
      customPadding={padding}
      customBorderRadius={borderRadius}
      {...props}
    >
      {children}
    </StyledSurface>
  );
};

export default Surface;
