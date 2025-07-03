import React from 'react';
import { render, screen } from '@testing-library/react';
import HomePage from '../pages/HomePage';

describe('Home Component', () => {
  it('renders hero section', () => {
    render(<HomePage />);
    expect(screen.getByRole('heading', { name: /algorithmic trading/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /launch app/i })).toBeInTheDocument();
  });
});
