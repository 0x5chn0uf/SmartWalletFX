import React from 'react';
import { Card as MuiCard, CardProps as MuiCardProps } from '@mui/material';
import { styled } from '@mui/material/styles';
import * as tokens from '../../../theme/generated';

export interface CardProps extends Omit<MuiCardProps, 'elevation'> {
  elevation?: 'none' | 'low' | 'medium' | 'high';
  padding?: 'none' | 'small' | 'medium' | 'large';
}

const StyledCard = styled(MuiCard)<{
  customElevation?: 'none' | 'low' | 'medium' | 'high';
  customPadding?: 'none' | 'small' | 'medium' | 'large';
}>(({ theme, customElevation = 'medium', customPadding = 'medium' }) => {
  const getElevationStyles = () => {
    switch (customElevation) {
      case 'none':
        return {
          boxShadow: 'none',
          backgroundColor: tokens.ColorBackgroundSurface,
        };
      case 'low':
        return {
          boxShadow: tokens.Elevation1,
          backgroundColor: tokens.ColorBackgroundSurface,
        };
      case 'high':
        return {
          boxShadow: tokens.Elevation4,
          backgroundColor: tokens.ColorBackgroundElevated,
        };
      default: // medium
        return {
          boxShadow: tokens.Elevation2,
          backgroundColor: tokens.ColorBackgroundSurface,
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

  return {
    fontFamily: tokens.FontFamilyPrimary,
    borderRadius: tokens.SizeRadiiMd,
    border: `1px solid ${theme.palette.divider}`,
    transition: 'all 0.2s ease-in-out',
    ...getElevationStyles(),
    ...getPaddingStyles(),
    '&:hover': {
      boxShadow: customElevation === 'none' ? tokens.Elevation1 : tokens.Elevation3,
    },
  };
});

export const Card: React.FC<CardProps> = ({
  children,
  elevation = 'medium',
  padding = 'medium',
  ...props
}) => {
  return (
    <StyledCard customElevation={elevation} customPadding={padding} {...props}>
      {children}
    </StyledCard>
  );
};

export default Card;
