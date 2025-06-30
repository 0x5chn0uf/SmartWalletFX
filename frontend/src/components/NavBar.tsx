import React from 'react';
import styled from '@emotion/styled';
import { Link as RouterLink, useLocation } from 'react-router-dom';

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(26, 31, 46, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  position: sticky;
  top: 0;
  z-index: 10;

  @media (max-width: 768px) {
    padding: 16px;
    flex-direction: column;
    gap: 16px;
  }
`;

const Logo = styled(RouterLink)`
  color: #4fd1c7;
  text-decoration: none;
  font-weight: 800;
  font-size: 24px;
  letter-spacing: -0.02em;
  text-shadow: 0 2px 8px rgba(79, 209, 199, 0.2);
`;

const Nav = styled.nav`
  display: flex;
  gap: 32px;
  align-items: center;
`;

const NavLink = styled(RouterLink)`
  color: #9ca3af;
  text-decoration: none;
  font-weight: 600;
  font-size: 16px;
  transition: color 0.2s;
  cursor: pointer;

  &:hover {
    color: #4fd1c7;
  }
`;

const LoginLink = styled(RouterLink)`
  color: #9ca3af;
  text-decoration: none;
  font-weight: 600;
  font-size: 16px;
  transition: color 0.2s;

  &:hover {
    color: #4fd1c7;
  }
`;

const NavBar: React.FC = () => {
  const location = useLocation();
  if (location.pathname === '/' || location.pathname === '/login-register') return null;
  return (
    <Header>
      <Logo to="/">SmartWalletFX</Logo>
      <Nav>
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/defi">DeFi Tracker</NavLink>
        <NavLink to="/wallets">Wallets</NavLink>
        <LoginLink to="/login-register">Login</LoginLink>
      </Nav>
    </Header>
  );
};

export default NavBar;
