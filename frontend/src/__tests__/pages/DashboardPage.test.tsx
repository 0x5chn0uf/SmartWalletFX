import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import dashboardReducer from '../../store/dashboardSlice';
import DashboardPage from '../../pages/DashboardPage';
import { RootState } from '../../store';

describe('DashboardPage', () => {
  function renderWithStore(preloadedState?: Partial<RootState>) {
    const store = configureStore({
      reducer: { dashboard: dashboardReducer },
      preloadedState,
    });
    return render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    );
  }

  it('renders dashboard summary cards', () => {
    renderWithStore({ dashboard: { overview: null, status: 'idle', error: null } });
    expect(screen.getByText(/total wallets/i)).toBeInTheDocument();
    expect(screen.getByText(/total balance/i)).toBeInTheDocument();
  });
});
