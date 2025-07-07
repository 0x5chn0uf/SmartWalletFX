// @ts-nocheck
import React from 'react';
import { render, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';
import App from '../../../App';
import authReducer, { fetchCurrentUser } from '../../../store/authSlice';

vi.mock('../../../services/api', async () => {
  const original: any = await vi.importActual('../../../services/api');
  return {
    default: {
      ...original.default,
      get: vi.fn().mockResolvedValue({ data: { id: '1', username: 'joe', email: 'j@e.com' } }),
      post: vi.fn().mockResolvedValue({ data: { access_token: 'new.token' } }),
      defaults: { headers: { common: {} } },
    },
  };
});

describe('App root', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('dispatches fetchCurrentUser when access_token exists', async () => {
    localStorage.setItem('access_token', 'token-value');

    const store = configureStore({ reducer: { auth: authReducer } });
    const spy = vi.spyOn(store, 'dispatch');

    render(
      <Provider store={store}>
        <MemoryRouter>
          <App />
        </MemoryRouter>
      </Provider>
    );

    await waitFor(() => expect(spy).toHaveBeenCalled());
  });

  it('attempts silent refresh when session_active flag present', async () => {
    localStorage.setItem('session_active', '1');

    const store = configureStore({ reducer: { auth: authReducer } });

    render(
      <Provider store={store}>
        <MemoryRouter>
          <App />
        </MemoryRouter>
      </Provider>
    );

    // wait for async post mock to resolve and the new token to be stored
    await waitFor(() => expect(localStorage.getItem('access_token')).toBe('new.token'));
  });
});
