import React from 'react';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from '../../components/ErrorBoundary';

describe('ErrorBoundary', () => {
  it('renders fallback UI when a child throws', () => {
    // Component that throws
    const ProblemChild = () => {
      throw new Error('Test error');
    };
    render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });
}); 