import React from 'react';
import styled from '@emotion/styled';
import { Link as RouterLink, useLocation } from 'react-router-dom';

// Styled components
const NavBar = styled.nav`
  background-color: var(--nav-background);
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
`;

const NavContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Logo = styled(RouterLink)`
  color: var(--color-primary);
  font-size: 1.5rem;
  font-weight: 700;
  text-decoration: none;
`;

const NavLinks = styled.div`
  display: flex;
  gap: 1.5rem;
  align-items: center;

  @media (max-width: 768px) {
    display: none;
  }
`;

const NavLink = styled(RouterLink)<{ $active?: boolean }>`
  color: var(--text-secondary);
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  transition: all 0.2s;

  &:hover {
    background-color: var(--nav-hover);
    color: var(--text-primary);
  }

  ${props =>
    props.$active &&
    `
        color: var(--color-primary);
        background-color: rgba(79, 209, 199, 0.1);
    `}
`;

const ConnectButton = styled.button`
  background-color: var(--color-primary);
  color: var(--nav-background);
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  border: none;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;

  &:hover {
    opacity: 0.9;
  }
`;

interface StyledNavBarProps {
  onConnectWallet?: () => void;
}

const StyledNavBar: React.FC<StyledNavBarProps> = ({ onConnectWallet }) => {
  const location = useLocation();

  // Hide navbar on landing/login page if needed
  if (location.pathname === '/' || location.pathname === '/login-register') return null;

  return (
    <NavBar>
      <NavContainer>
        <Logo to="/">Trading Bot</Logo>
        <NavLinks>
          <NavLink to="/" $active={location.pathname === '/'}>
            Home
          </NavLink>
          <NavLink to="/dashboard" $active={location.pathname === '/dashboard'}>
            Dashboard
          </NavLink>
          <NavLink to="/defi" $active={location.pathname === '/defi'}>
            DeFi
          </NavLink>
          <NavLink to="/wallets" $active={location.pathname === '/wallets'}>
            Wallets
          </NavLink>
          <ConnectButton onClick={onConnectWallet}>Connect Wallet</ConnectButton>
        </NavLinks>
      </NavContainer>
    </NavBar>
  );
};

export default StyledNavBar;
