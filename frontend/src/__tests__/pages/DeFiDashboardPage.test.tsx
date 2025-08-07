import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../../theme';
import { store } from '../../store';
import DeFiDashboardPage from '../../pages/DeFiDashboardPage';

describe('DeFiDashboardPage', () => {
  it('renders static dashboard sections', () => {
    render(
      <Provider store={store}>
        <ThemeProvider theme={createAppTheme()}>
          <MemoryRouter initialEntries={['/defi/0x123...']}>
            <DeFiDashboardPage />
          </MemoryRouter>
        </ThemeProvider>
      </Provider>
    );
    expect(screen.getByText(/Total Portfolio Value/i)).toBeInTheDocument();
    expect(screen.getByText(/Portfolio Performance/i)).toBeInTheDocument();
  });
});
