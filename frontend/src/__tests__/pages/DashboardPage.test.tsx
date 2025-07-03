import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import dashboardReducer from '../../store/dashboardSlice';
import DashboardPage from '../../pages/DashboardPage';
import { RootState } from '../../store';
import { vi } from 'vitest';

beforeAll(() => {
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as any;
});

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
    renderWithStore({
      dashboard: {
        overview: {
          totalWallets: 0,
          totalBalance: 0,
          dailyVolume: 0,
          chart: [],
          portfolioDistribution: [],
        },
        status: 'succeeded',
        error: null,
      },
    });
    expect(screen.getByText(/total wallets/i)).toBeInTheDocument();
    expect(screen.getByText(/total balance/i)).toBeInTheDocument();
  });
});
