import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';
import { ThemeProvider } from './providers/ThemeProvider';

test('renders navigation links', () => {
  // ensure the NavBar is visible by navigating to dashboard route
  window.history.pushState({}, '', '/dashboard');

  render(
    <ThemeProvider>
      <App />
    </ThemeProvider>
  );

  expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /portfolio/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument();
});
