import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import walletDetailReducer from '../../store/walletDetailSlice';
import WalletDetailPage from '../../pages/WalletDetailPage';

describe('WalletDetailPage', () => {
  function renderWithStore(preloadedState: any) {
    const store = configureStore({
      reducer: { walletDetail: walletDetailReducer },
      preloadedState,
    });
    return render(
      <Provider store={store}>
        <WalletDetailPage />
      </Provider>
    );
  }

  it('renders wallet detail page', () => {
    renderWithStore({ walletDetail: { wallet: { id: '1', name: 'Test Wallet', balance: 1000, currency: 'USD' }, transactions: [], status: 'idle', error: null } });
    expect(screen.getByText(/wallet/i)).toBeInTheDocument();
  });
}); 