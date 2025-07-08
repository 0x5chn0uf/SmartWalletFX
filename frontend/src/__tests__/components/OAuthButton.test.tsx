import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OAuthButton } from '../../components/oauth/OAuthButton';
import { describe, it, expect, vi } from 'vitest';

describe('OAuthButton', () => {
  it('renders correct label', () => {
    render(<OAuthButton provider="google" />);
    const btn = screen.getByRole('button');
    expect(btn).toHaveTextContent('Continue with Google');
    expect(btn.querySelector('svg')).not.toBeNull();
  });

  it('redirects to provider login on click and calls handler', async () => {
    const onClick = vi.fn();
    const original = window.location;
    delete (window as any).location;
    (window as any).location = { href: '' };
    render(<OAuthButton provider="github" onClick={onClick} />);
    await userEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalled();
    expect(window.location.href).toBe('/auth/oauth/github/login');
    window.location = original;
  });
});
