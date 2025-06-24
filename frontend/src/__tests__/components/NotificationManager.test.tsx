import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import notificationReducer from '../../store/notificationSlice';
import NotificationManager from '../../components/NotificationManager';

type NotificationState = {
  notification: {
    notifications: Array<{
      id: string;
      message: string;
      severity: string;
      autoHideDuration?: number;
    }>;
  };
};

describe('NotificationManager', () => {
  function renderWithStore(preloadedState: NotificationState) {
    const store = configureStore({
      reducer: { notification: notificationReducer },
      preloadedState,
    });
    return render(
      <Provider store={store}>
        <NotificationManager />
      </Provider>
    );
  }

  it('renders nothing when there are no notifications', () => {
    renderWithStore({ notification: { notifications: [] } });
    // Should not find any Toast
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('renders notifications from the store', () => {
    const notifications = [
      {
        id: '1',
        message: 'Test notification',
        severity: 'info',
        autoHideDuration: 3000,
      },
    ];
    renderWithStore({ notification: { notifications } });
    expect(screen.getByText('Test notification')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
}); 