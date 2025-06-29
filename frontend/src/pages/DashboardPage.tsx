import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Paper, Typography } from '@mui/material';
import SummaryCard from '../components/SummaryCard';
import BalanceAreaChart from '../components/BalanceAreaChart';
import ChartSkeleton from '../components/ChartSkeleton';
import PortfolioDistributionChart from '../components/PortfolioDistributionChart';
import { fetchDashboardOverview } from '../store/dashboardSlice';
import { RootState, AppDispatch } from '../store';
import useNotification from '../hooks/useNotification';

// Icons
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';

const DashboardPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { overview, status } = useSelector((state: RootState) => state.dashboard);
  const { showError } = useNotification();

  useEffect(() => {
    if (status === 'idle') {
      dispatch(fetchDashboardOverview()).catch(() => {
        showError('Failed to load dashboard data. Please try again.');
      });
    }
  }, [dispatch, status, showError]);

  const isLoading = status === 'loading' || (status === 'idle' && !overview);

  const formatCurrency = (value: number | undefined) => {
    if (value === undefined) return '—';
    return `$${value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  const cards = [
    {
      title: 'Total Wallets',
      value: overview?.totalWallets ?? '—',
      icon: <AccountBalanceWalletIcon fontSize="inherit" />,
    },
    {
      title: 'Total Balance',
      value: formatCurrency(overview?.totalBalance),
      icon: <AttachMoneyIcon fontSize="inherit" />,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-10 px-2">
      <div className="max-w-5xl mx-auto flex flex-col gap-8">
        {/* Header: Title and actions */}
        <div className="flex items-center justify-between gap-4">
          <Typography
            variant="h4"
            component="h1"
            className="font-bold text-gray-800 dark:text-gray-100"
          >
            Dashboard
          </Typography>
          {/* Place for future actions (e.g., profile/settings button) */}
        </div>

        {/* KPI Cards */}
        <div className="flex flex-wrap justify-center gap-6">
          {cards.map(c => (
            <div
              key={c.title}
              className="w-full sm:w-auto max-w-xs"
              style={{ minWidth: '16rem', maxWidth: '18rem' }}
            >
              <SummaryCard title={c.title} value={c.value} loading={isLoading} icon={c.icon} />
            </div>
          ))}
        </div>

        {/* Balance Over Time Chart */}
        <Paper className="p-4">
          <Typography variant="h6" gutterBottom>
            Balance Over Time
          </Typography>
          {isLoading ? (
            <ChartSkeleton />
          ) : overview?.chart ? (
            <BalanceAreaChart data={overview.chart} />
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              No chart data available.
            </div>
          )}
        </Paper>

        {/* Portfolio Distribution Chart */}
        <Paper className="p-4">
          <Typography variant="h6" gutterBottom>
            Portfolio Distribution
          </Typography>
          {isLoading ? (
            <ChartSkeleton />
          ) : overview?.portfolioDistribution ? (
            <PortfolioDistributionChart data={overview.portfolioDistribution} />
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              No portfolio data available.
            </div>
          )}
        </Paper>
      </div>
    </div>
  );
};

export default DashboardPage;
