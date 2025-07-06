import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../theme';
import LoginRegisterPage from '../../../pages/LoginRegisterPage';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { Provider } from 'react-redux';
import { store } from '../../../store';

// Mock useNavigate to avoid actual navigation during tests
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<any>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

// Stub global alert
vi.stubGlobal('alert', vi.fn());

describe('LoginRegisterPage', () => {
  const theme = createAppTheme();

  const setup = () => {
    render(
      <Provider store={store}>
        <ThemeProvider theme={theme}>
          <MemoryRouter>
            <LoginRegisterPage />
          </MemoryRouter>
        </ThemeProvider>
      </Provider>
    );
  };

  it('shows login form by default', () => {
    setup();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('switches to register tab and shows error on mismatched passwords', () => {
    setup();
    // Click the Register tab
    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    // Fill registration fields
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByPlaceholderText(/create a password/i), {
      target: { value: 'secret1' },
    });
    fireEvent.change(screen.getByPlaceholderText(/confirm your password/i), {
      target: { value: 'secret2' },
    });

    // Submit the form
    // The page has two "Register" buttons (tab and submit). Pick the submit button (type submit)
    const submitButtons = screen.getAllByRole('button', { name: /^register$/i });
    const submitBtn =
      submitButtons.find(btn => btn.getAttribute('type') === 'submit') ?? submitButtons[1];
    fireEvent.click(submitBtn);

    expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
  });
});
