import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MemoryRouter } from 'react-router-dom';
import walletsReducer from '../../store/walletsSlice';
import WalletList from '../../pages/WalletList';
import { RootState } from '../../store';

describe('WalletList Page', () => {
  function renderWithStore(preloadedState?: Partial<RootState>) {
    const store = configureStore({
      reducer: { wallets: walletsReducer },
      preloadedState,
    });

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

    expect(screen.getByText(/wallets/i)).toBeInTheDocument();
  });
});
