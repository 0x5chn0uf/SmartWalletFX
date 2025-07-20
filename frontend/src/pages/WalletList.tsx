import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import styled from '@emotion/styled';
import { RootState, AppDispatch } from '../store';
import { fetchWallets, setSearch, setPage } from '../store/walletsSlice';
import WalletTable from '../components/WalletTable';
import Pagination from '../components/Pagination';
import useNotification from '../hooks/useNotification';
import StatsCards from '../components/StatsCards';
import PortfolioDistributionChart from '../components/PortfolioDistributionChart';
import WalletConnectCTA from '../components/home/WalletConnectCTA';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
`;

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 600;
  margin: 2rem 0 1rem 0;
  color: #1f2937;
`;

const SearchInput = styled.input`
  width: 100%;
  max-width: 400px;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
  margin-bottom: 2rem;
  transition: border-color 0.2s;

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  &::placeholder {
    color: #9ca3af;
  }
`;

const SearchBox = styled.div`
  margin-bottom: 2rem;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;

  &::after {
    content: '';
    width: 40px;
    height: 40px;
    border: 4px solid #f3f4f6;
    border-top: 4px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

const ErrorAlert = styled.div`
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 2rem;
`;

const GridContainer = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const MainContent = styled.div``;

const Sidebar = styled.div``;

const WalletList: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { wallets, total, page, limit, search, status, error } = useSelector(
    (state: RootState) => state.wallets
  );
  const [searchInput, setSearchInput] = useState(search);
  const { showError } = useNotification();

  useEffect(() => {
    dispatch(fetchWallets({ page, limit, search })).catch(_err => {
      showError('Failed to load wallets');
    });
  }, [dispatch, page, limit, search, showError]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    dispatch(setSearch(searchInput));
    dispatch(setPage(1));
  };

  const handlePageChange = (newPage: number) => {
    dispatch(setPage(newPage));
  };

  if (status === 'loading') {
    return (
      <Container>
        <LoadingSpinner />
      </Container>
    );
  }

  return (
    <Container>
      <Title>My Wallets</Title>

      <SearchBox>
        <form onSubmit={handleSearchSubmit}>
          <SearchInput
            type="text"
            placeholder="Search wallets..."
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
          />
        </form>
      </SearchBox>

      {status === 'failed' && error && <ErrorAlert>Error loading wallets: {error}</ErrorAlert>}

      <StatsCards />

      <GridContainer>
        <MainContent>
          <WalletTable wallets={wallets} />
          <Pagination page={page} total={total} limit={limit} onPageChange={handlePageChange} />
        </MainContent>
        <Sidebar>
          <PortfolioDistributionChart data={wallets} />
        </Sidebar>
      </GridContainer>

      <WalletConnectCTA />
    </Container>
  );
};

export default WalletList;
