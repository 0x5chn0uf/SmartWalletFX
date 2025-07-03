import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../../theme';
import {
  PortfolioFilter,
  PortfolioFilterType,
} from '../../../../components/PortfolioFilter/PortfolioFilter';
import { describe, it, expect, vi } from 'vitest';

describe('PortfolioFilter', () => {
  const theme = createAppTheme();

  const setup = (value: PortfolioFilterType = 'all', onChange = vi.fn()) => {
    render(
      <ThemeProvider theme={theme}>
        <PortfolioFilter value={value} onChange={onChange} />
      </ThemeProvider>
    );
    return { onChange };
  };

  it('renders all toggle buttons', () => {
    setup();
    expect(screen.getByRole('button', { name: /all/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /spot/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /defi/i })).toBeInTheDocument();
  });

  it('calls onChange with correct value when a toggle button is clicked', async () => {
    const user = userEvent.setup();
    const { onChange } = setup('all');

    await user.click(screen.getByRole('button', { name: /spot/i }));

    expect(onChange).toHaveBeenCalledWith('spot');
  });

  it('does not call onChange when the same value is clicked again', async () => {
    const user = userEvent.setup();
    const { onChange } = setup('all');

    await user.click(screen.getByRole('button', { name: /all/i }));

    expect(onChange).not.toHaveBeenCalled();
  });
});
