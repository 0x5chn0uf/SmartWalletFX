import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../../../theme';
import { WalletSelector } from '../../../../components/Timeline/WalletInput';
import { describe, it, expect, vi, beforeEach } from 'vitest';

const VALID_ADDRESS = '0x1234567890123456789012345678901234567890';
const INVALID_ADDRESS = '0x123';

describe('WalletSelector', () => {
  const theme = createAppTheme();
  let onChange: ReturnType<typeof vi.fn>;

  const setup = (address = '') => {
    onChange = vi.fn();
    render(
      <ThemeProvider theme={theme}>
        <WalletSelector address={address} options={[VALID_ADDRESS]} onChange={onChange} />
      </ThemeProvider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows error for invalid address', async () => {
    const user = userEvent.setup();
    setup();

    const input = screen.getByLabelText(/wallet address/i);
    await user.type(input, INVALID_ADDRESS);

    expect(await screen.findByText(/invalid ethereum address/i)).toBeInTheDocument();
    expect(onChange).not.toHaveBeenCalled();
  });

  it('calls onChange for valid address', async () => {
    const user = userEvent.setup();
    setup();

    const input = screen.getByLabelText(/wallet address/i);
    await user.type(input, VALID_ADDRESS);

    expect(onChange).toHaveBeenCalledWith(VALID_ADDRESS);
  });
});
