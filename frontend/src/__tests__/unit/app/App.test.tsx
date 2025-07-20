import React from 'react';
import { render, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Global, css } from '@emotion/react';
import { vi } from 'vitest';
import { AppContent } from '../../../App';
import authReducer, { fetchCurrentUser } from '../../../store/authSlice';
import notificationReducer from '../../../store/notificationSlice';

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
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  const globalStyles = css`
    * {
      box-sizing: border-box;
    }
  `;

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('dispatches fetchCurrentUser when session_active flag exists', async () => {
    localStorage.setItem('session_active', '1');

    const store = configureStore({
      reducer: {
        auth: authReducer,
        notification: notificationReducer,
      },
    });
    const spy = vi.spyOn(store, 'dispatch');

    render(
      <Provider store={store}>
        <Global styles={globalStyles} />
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <AppContent />
          </MemoryRouter>
        </QueryClientProvider>
      </Provider>
    );

    await waitFor(() => {
      const fetchCurrentUserActions = spy.mock.calls.filter(
        call =>
          call[0]?.type === fetchCurrentUser.pending.type ||
          call[0]?.type === fetchCurrentUser.fulfilled.type
      );
      expect(fetchCurrentUserActions.length).toBeGreaterThan(0);
    });
  });

  it('attempts fallback silent refresh when fetchCurrentUser fails', async () => {
    localStorage.setItem('session_active', '1');

    // Mock fetchCurrentUser to fail initially
    const apiClient = await import('../../../services/api');
    apiClient.default.get = vi
      .fn()
      .mockRejectedValueOnce(new Error('Auth failed'))
      .mockResolvedValueOnce({ data: { id: '1', username: 'joe', email: 'j@e.com' } });

    const store = configureStore({
      reducer: {
        auth: authReducer,
        notification: notificationReducer,
      },
    });

    render(
      <Provider store={store}>
        <Global styles={globalStyles} />
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <AppContent />
          </MemoryRouter>
        </QueryClientProvider>
      </Provider>
    );

    // Wait for the refresh process to complete
    await waitFor(() => {
      expect(apiClient.default.post).toHaveBeenCalledWith(
        '/auth/refresh',
        {},
        { withCredentials: true }
      );
    });
  });
});
