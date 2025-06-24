import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import SummaryCard from '../components/SummaryCard';
import BalanceAreaChart from '../components/BalanceAreaChart';
import ChartPlaceholder from '../components/ChartPlaceholder';
import { fetchDashboardOverview } from '../store/dashboardSlice';
import { RootState, AppDispatch } from '../store';
import useNotification from '../hooks/useNotification';

const DashboardPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { overview, status, error } = useSelector((state: RootState) => state.dashboard);
  const { showError } = useNotification();

  useEffect(() => {
    if (status === 'idle') {
      dispatch(fetchDashboardOverview()).catch((err) => {
        showError('Failed to load dashboard data. Please try again.');
      });
    }
  }, [dispatch, status, showError]);

  const cards = [
    { title: 'Total Wallets', value: overview?.totalWallets ?? '—' },
    { title: 'Total Balance', value: overview ? `$${overview.totalBalance}` : '—' },
    { title: '24h Volume', value: overview ? `$${overview.dailyVolume}` : '—' },
  ];

  return (
    <div className="p-4 space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {cards.map((c) => (
          <SummaryCard key={c.title} title={c.title} value={c.value} />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {overview ? (
          <BalanceAreaChart data={overview.chart} />
        ) : (
          <ChartPlaceholder />
        )}
        <ChartPlaceholder />
      </div>
    </div>
  );
};

export default DashboardPage;
