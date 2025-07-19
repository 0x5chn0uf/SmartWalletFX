import React from 'react';
import { renderHook } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import useAuth from '../../hooks/useAuth';
import authReducer from '../../store/authSlice';

describe('useAuth hook', () => {
  it('returns auth slice from store', () => {
    const preloadedState = {
      auth: {
        isAuthenticated: true,
        user: { id: '1', username: 'a', email: 'e' },
        status: 'idle',
        error: null,
      },
    };

    const store = configureStore({ reducer: { auth: authReducer }, preloadedState } as any);

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.username).toBe('a');
  });
});
