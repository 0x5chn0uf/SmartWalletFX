import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../../App';

describe('App Component', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByText(/learn react/i)).toBeInTheDocument();
  });

  it('displays the header', () => {
    render(<App />);
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });
}); 