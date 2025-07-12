import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import VerifyEmailNoticePage from '../../pages/VerifyEmailNoticePage';

describe('VerifyEmailNoticePage', () => {
  it('renders info and navigate button', () => {
    render(
      <MemoryRouter>
        <VerifyEmailNoticePage />
      </MemoryRouter>
    );
    expect(
      screen.getByText(/verification email has been sent/i)
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /back to login/i }));
  });
});
