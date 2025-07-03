import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import walletsReducer from '../../store/walletsSlice';
import WalletList from '../../pages/WalletList';
import { RootState } from '../../store';
import apiClient from '../../services/api';

beforeAll(() => {
  // jsdom doesn't implement ResizeObserver which MUI's Table relies on
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as any;
  vi.spyOn(apiClient, 'get').mockResolvedValue({ data: { wallets: [], total: 0, page: 1, limit: 10 } });
});

describe('WalletList Page', () => {
  function renderWithStore(preloadedState?: Partial<RootState>) {
    const store = configureStore({
      reducer: { wallets: walletsReducer },
      preloadedState,
    });
    // Prevent network calls triggered by useEffect
    vi.spyOn(store, 'dispatch').mockImplementation(() => Promise.resolve());

    return render(
      <Provider store={store}>
        <MemoryRouter>
          <WalletList />
        </MemoryRouter>
      </Provider>
    );
  }

  it('renders wallet list page', () => {
    renderWithStore({
      wallets: {
        wallets: [
          {
            id: '1',
            name: 'Test Wallet',
            balance: 1000,
            address: '0x123',
            currency: 'USD',
            lastUpdated: '2024-01-01',
          },
        ],
        total: 1,
        page: 1,
        limit: 10,
        search: '',
        status: 'succeeded',
        error: null,
      },
    });

    expect(screen.getAllByText(/wallets/i)[0]).toBeInTheDocument();
  });
});
