import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import { ThemeProvider } from './providers/ThemeProvider';

test('renders navigation links', () => {
  render(
    <ThemeProvider>
      <App />
    </ThemeProvider>,
  );
  const dashboardLink = screen.getByText(/Dashboard/i);
  const walletsLink = screen.getByText(/Wallets/i);
  expect(dashboardLink).toBeInTheDocument();
  expect(walletsLink).toBeInTheDocument();
});
