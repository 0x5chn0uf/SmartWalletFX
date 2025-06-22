import React from 'react';
import { Box, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';

export type PortfolioFilterType = 'all' | 'spot' | 'defi';

interface PortfolioFilterProps {
  value: PortfolioFilterType;
  onChange: (newValue: PortfolioFilterType) => void;
}

export const PortfolioFilter: React.FC<PortfolioFilterProps> = ({ value, onChange }) => {
  const handleChange = (
    event: React.MouseEvent<HTMLElement>,
    newFilter: PortfolioFilterType | null
  ) => {
    if (newFilter !== null) {
      onChange(newFilter);
    }
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
      <Typography variant="body2" sx={{ mr: 2 }}>
        Filter by:
      </Typography>
      <ToggleButtonGroup
        value={value}
        exclusive
        onChange={handleChange}
        aria-label="portfolio filter"
        size="small"
      >
        <ToggleButton value="all" aria-label="all portfolios">
          All
        </ToggleButton>
        <ToggleButton value="spot" aria-label="spot holdings">
          Spot
        </ToggleButton>
        <ToggleButton value="defi" aria-label="defi positions">
          DeFi
        </ToggleButton>
      </ToggleButtonGroup>
    </Box>
  );
}; 