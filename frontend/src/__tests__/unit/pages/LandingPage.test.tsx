import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../theme';
import LandingPage from '../../../pages/LandingPage';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeAll } from 'vitest';

// Mock WalletPreview to avoid complex internal logic
vi.mock('../../../components/WalletPreview', () => ({
  default: () => <div data-testid="wallet-preview" />,
}));

describe('LandingPage', () => {
  const theme = createAppTheme();

  const setup = () => {
    render(
      <ThemeProvider theme={theme}>
        <MemoryRouter>
          <LandingPage />
        </MemoryRouter>
      </ThemeProvider>
    );
  };

  it('renders hero title and call to action button', () => {
    setup();
    expect(screen.getByRole('heading', { name: /track\. analyze\. grow\./i })).toBeInTheDocument();
    const cta = screen.getByRole('link', { name: /start tracking/i });
    expect(cta).toBeInTheDocument();
    expect(cta).toHaveAttribute('href', '/login-register');
  });

  it('renders all feature cards', () => {
    setup();
    const featureTitles = [
      'Unified Dashboard',
      'Performance Metrics',
      'Alerts & Notifications',
      'Secure Sync',
    ];
    featureTitles.forEach(title => {
      expect(screen.getByText(title)).toBeInTheDocument();
    });
  });
});
