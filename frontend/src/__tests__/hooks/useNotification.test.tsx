import { renderHook, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import notificationReducer from '../../store/notificationSlice';
import useNotification from '../../hooks/useNotification';

describe('useNotification', () => {
  function wrapper({ children }: { children: React.ReactNode }) {
    const store = configureStore({
      reducer: { notification: notificationReducer },
      preloadedState: { notification: { notifications: [] } },
    });
    return <Provider store={store}>{children}</Provider>;
  }

  it('returns showSuccess and showError functions', () => {
    const { result } = renderHook(() => useNotification(), { wrapper });
    expect(typeof result.current.showSuccess).toBe('function');
    expect(typeof result.current.showError).toBe('function');
  });

  it('showSuccess and showError do not throw', () => {
    const { result } = renderHook(() => useNotification(), { wrapper });
    act(() => {
      result.current.showSuccess('Success message');
      result.current.showError('Error message');
    });
  });
});
