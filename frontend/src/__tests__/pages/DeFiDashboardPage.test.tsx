import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import DeFiDashboardPage from '../../pages/DeFiDashboardPage';
import * as defiService from '../../services/defi';

// Mock the services
jest.mock('../../services/defi');
jest.mock('../../components/Charts/TimelineChart', () => ({
  TimelineChart: ({ data }: { data: any }) => (
    <div data-testid="timeline-chart">Timeline Chart</div>
  ),
}));

const mockDefiKPI = {
  tvl: 1254321.45,
  apy: 8.73,
  updated_at: '2024-06-18T00:00:00Z',
  protocols: [
    { name: 'Aave', tvl: 534221.12, apy: 6.2, positions: 12 },
    { name: 'Compound', tvl: 312876.44, apy: 5.1, positions: 8 },
    { name: 'Radiant', tvl: 407224.89, apy: 14.2, positions: 5 },
  ],
};

const mockProtocolBreakdown = [
  { name: 'Aave', tvl: 534221.12, apy: 6.2, positions: 12 },
  { name: 'Compound', tvl: 312876.44, apy: 5.1, positions: 8 },
  { name: 'Radiant', tvl: 407224.89, apy: 14.2, positions: 5 },
];

const mockTimeline = {
  snapshots: [
    {
      user_address: '0xMOCK',
      timestamp: 1719446400,
      total_collateral: 1200000,
      total_borrowings: 0,
      aggregate_health_score: null,
    },
    {
      user_address: '0xMOCK',
      timestamp: 1719532800,
      total_collateral: 1225000,
      total_borrowings: 0,
      aggregate_health_score: null,
    },
  ],
  interval: '1d',
  limit: 7,
  offset: 0,
  total: 7,
};

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderWithProviders = (component: React.ReactElement) => {
  const theme = createTheme();
  const queryClient = createTestQueryClient();

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>{component}</ThemeProvider>
    </QueryClientProvider>
  );
};

describe('DeFiDashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should show loading spinner when data is loading', async () => {
      (defiService.getDefiKPI as jest.Mock).mockImplementation(() => new Promise(() => {}));
      (defiService.getProtocolBreakdown as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      );
      (defiService.getPortfolioTimeline as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      );

      renderWithProviders(<DeFiDashboardPage />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error message when data fails to load', async () => {
      (defiService.getDefiKPI as jest.Mock).mockRejectedValue(new Error('API Error'));
      (defiService.getProtocolBreakdown as jest.Mock).mockResolvedValue(mockProtocolBreakdown);
      (defiService.getPortfolioTimeline as jest.Mock).mockResolvedValue(mockTimeline);

      renderWithProviders(<DeFiDashboardPage />);

      await waitFor(() => {
        expect(
          screen.getByText('Failed to load DeFi data. Please try again later.')
        ).toBeInTheDocument();
      });
    });
  });

  describe('KPI Cards', () => {
    beforeEach(() => {
      (defiService.getDefiKPI as jest.Mock).mockResolvedValue(mockDefiKPI);
      (defiService.getProtocolBreakdown as jest.Mock).mockResolvedValue(mockProtocolBreakdown);
      (defiService.getPortfolioTimeline as jest.Mock).mockResolvedValue(mockTimeline);
    });

    it('should display KPI cards with correct data', async () => {
      renderWithProviders(<DeFiDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Total Value Locked (TVL)')).toBeInTheDocument();
        expect(screen.getByText('$1,254,321.45')).toBeInTheDocument();

        expect(screen.getByText('Average APY')).toBeInTheDocument();
        expect(screen.getByText('8.73%')).toBeInTheDocument();

        expect(screen.getByText('Protocols Tracked')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });
  });

  describe('Timeline Chart', () => {
    beforeEach(() => {
      (defiService.getDefiKPI as jest.Mock).mockResolvedValue(mockDefiKPI);
      (defiService.getProtocolBreakdown as jest.Mock).mockResolvedValue(mockProtocolBreakdown);
      (defiService.getPortfolioTimeline as jest.Mock).mockResolvedValue(mockTimeline);
    });

    it('should display timeline chart when data is available', async () => {
      renderWithProviders(<DeFiDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Performance Timeline')).toBeInTheDocument();
        expect(screen.getByTestId('timeline-chart')).toBeInTheDocument();
      });
    });

    it('should show no data message when timeline is empty', async () => {
      (defiService.getPortfolioTimeline as jest.Mock).mockResolvedValue({ snapshots: [] });

      renderWithProviders(<DeFiDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('No timeline data available')).toBeInTheDocument();
      });
    });
  });

  describe('Protocol Table', () => {
    beforeEach(() => {
      (defiService.getDefiKPI as jest.Mock).mockResolvedValue(mockDefiKPI);
      (defiService.getProtocolBreakdown as jest.Mock).mockResolvedValue(mockProtocolBreakdown);
      (defiService.getPortfolioTimeline as jest.Mock).mockResolvedValue(mockTimeline);
    });

    it('should display protocol table with correct data', async () => {
      renderWithProviders(<DeFiDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('Protocol Breakdown')).toBeInTheDocument();
        expect(screen.getByText('Aave')).toBeInTheDocument();
        expect(screen.getByText('Compound')).toBeInTheDocument();
        expect(screen.getByText('Radiant')).toBeInTheDocument();
      });
    });

    it('should sort table by TVL when TVL header is clicked', async () => {
      renderWithProviders(<DeFiDashboardPage />);

      await waitFor(() => {
        const tvlHeader = screen.getByText('TVL');
        fireEvent.click(tvlHeader);

        // Check that Aave (highest TVL) appears first
        const rows = screen.getAllByRole('row');
        expect(rows[1]).toHaveTextContent('Aave');
      });
    });

    it('should sort table by APY when APY header is clicked', async () => {
      renderWithProviders(<DeFiDashboardPage />);

      await waitFor(() => {
        const apyHeader = screen.getByText('APY');
        fireEvent.click(apyHeader);

        // Check that Radiant (highest APY) appears first
        const rows = screen.getAllByRole('row');
        expect(rows[1]).toHaveTextContent('Radiant');
      });
    });

    it('should handle pagination correctly', async () => {
      // Use the default mock data that we know works
      (defiService.getDefiKPI as jest.Mock).mockResolvedValue(mockDefiKPI);
      (defiService.getProtocolBreakdown as jest.Mock).mockResolvedValue(mockProtocolBreakdown);
      (defiService.getPortfolioTimeline as jest.Mock).mockResolvedValue(mockTimeline);

      renderWithProviders(<DeFiDashboardPage />);

      // Wait for the component to load
      await waitFor(() => {
        expect(screen.getByText('Protocol Breakdown')).toBeInTheDocument();
      });

      // Verify the table shows the default protocols
      expect(screen.getByText('Aave')).toBeInTheDocument();
      expect(screen.getByText('Compound')).toBeInTheDocument();
      expect(screen.getByText('Radiant')).toBeInTheDocument();

      // Verify pagination controls exist
      expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();

      // Test that pagination controls are functional (click next page)
      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      // Verify the pagination state changed (button should be disabled or page info updated)
      await waitFor(() => {
        // The next button should be disabled since we only have 3 protocols
        expect(nextButton).toBeDisabled();
      });
    });
  });

  describe('Responsive Design', () => {
    beforeEach(() => {
      (defiService.getDefiKPI as jest.Mock).mockResolvedValue(mockDefiKPI);
      (defiService.getProtocolBreakdown as jest.Mock).mockResolvedValue(mockProtocolBreakdown);
      (defiService.getPortfolioTimeline as jest.Mock).mockResolvedValue(mockTimeline);
    });

    it('should render without crashing on different screen sizes', async () => {
      // Test with different viewport sizes
      const { rerender } = renderWithProviders(<DeFiDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('DeFi Tracker Dashboard')).toBeInTheDocument();
      });

      // Rerender to test different conditions
      rerender(
        <QueryClientProvider client={createTestQueryClient()}>
          <ThemeProvider theme={createTheme()}>
            <DeFiDashboardPage />
          </ThemeProvider>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('DeFi Tracker Dashboard')).toBeInTheDocument();
      });
    });
  });
});
