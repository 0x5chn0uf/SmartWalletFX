import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../../App';
import { ThemeProvider } from '../../providers/ThemeProvider';

describe('App Component', () => {
  it('renders navigation', () => {
    render(
      <ThemeProvider>
        <App />
      </ThemeProvider>
    );
    expect(screen.getByText(/Home/i)).toBeInTheDocument();
  });
});
