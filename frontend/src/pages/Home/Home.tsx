import React from 'react';
import { Typography, Box, CircularProgress } from '@mui/material';
import { Layout } from '../../components/Layout/Layout';
import { useTimeline } from '../../hooks/useTimeline';
import { TimelineChart } from '../../components/Charts/TimelineChart';
import { TimelineFilters, TimelineFilterValues } from '../../components/Timeline/TimelineFilters';
import { WalletSelector } from '../../components/Timeline/WalletInput';
import { getWallets } from '../../services/wallets';
import { mapSnapshotsToChartData } from '../../utils/timelineAdapter';
import { SmartTraderMoves } from '../../components/SmartTraderMoves/SmartTraderMoves';
import {
  PortfolioFilter,
  PortfolioFilterType,
} from '../../components/PortfolioFilter/PortfolioFilter';

export const Home: React.FC = () => {
  const nowDate = new Date();
  const oneMonthAgoDate = new Date(nowDate.getTime() - 30 * 24 * 60 * 60 * 1000);

  const [address, setAddress] = React.useState('0xmeta');
  const [portfolioFilter, setPortfolioFilter] = React.useState<PortfolioFilterType>('all');

  const [filters, setFilters] = React.useState<TimelineFilterValues>({
    from: oneMonthAgoDate.toISOString().slice(0, 10),
    to: nowDate.toISOString().slice(0, 10),
    interval: 'none' as 'none' | 'daily' | 'weekly',
  });

  const fromDateObj = new Date(filters.from);
  const toDateObj = new Date(filters.to);

  const isDateRangeValid =
    !Number.isNaN(fromDateObj.getTime()) &&
    !Number.isNaN(toDateObj.getTime()) &&
    fromDateObj <= toDateObj;

  const ETH_ADDRESS_REGEX = /^0x[a-fA-F0-9]{40}$/;
  const isAddressValid = ETH_ADDRESS_REGEX.test(address);

  const shouldFetch = isDateRangeValid && isAddressValid;

  const fromTs = Math.floor(fromDateObj.getTime() / 1000);
  const toTs = Math.floor(toDateObj.getTime() / 1000);

  const [walletOptions, setWalletOptions] = React.useState<string[]>([]);

  React.useEffect(() => {
    (async () => {
      try {
        const wallets = await getWallets();
        setWalletOptions(wallets);
      } catch (err) {
        // ignore fetch errors in UI for now
      }
    })();
  }, []);

  const { data, loading, error } = useTimeline({
    address,
    from: fromTs,
    to: toTs,
    interval: filters.interval,
    enabled: shouldFetch,
  });

  return (
    <Layout>
      <Box sx={{ py: 4 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          SmartWalletFX
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom>
          Your Smart Crypto Portfolio Tracker
        </Typography>

        <WalletSelector address={address} onChange={setAddress} options={walletOptions} />

        {!isAddressValid && (
          <Typography color="error" variant="body2" sx={{ mb: 2 }}>
            Enter a valid Ethereum address.
          </Typography>
        )}

        <TimelineFilters {...filters} onChange={newFilters => setFilters(newFilters)} />

        {!isDateRangeValid && (
          <Typography color="error" variant="body2" sx={{ mb: 2 }}>
            &quot;From&quot; date must be before &quot;To&quot; date.
          </Typography>
        )}

        <PortfolioFilter value={portfolioFilter} onChange={setPortfolioFilter} />

        {loading && <CircularProgress />}
        {error && <Typography color="error">{error}</Typography>}
        {data && data.length > 0 && (
          <TimelineChart data={mapSnapshotsToChartData(data)} metric="collateral" />
        )}

        <SmartTraderMoves />
      </Box>
    </Layout>
  );
};
