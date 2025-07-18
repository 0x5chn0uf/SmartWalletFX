import React from 'react';
import styled from '@emotion/styled';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { logoutUser } from '../store/authSlice';
import { AppDispatch } from '../store';

const Navbar = styled.nav`
  height: 80px;
  background: var(--color-surface);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 10;
`;

const Logo = styled(RouterLink)`
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--color-primary);
  text-decoration: none;
  margin-left: 0;
`;

const NavLinks = styled.div`
  display: flex;
  gap: 24px;
`;

const LogoutButton = styled.button`
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  padding: 12px 16px;
  border-radius: 8px;
  transition:
    background 0.2s,
    color 0.2s;
  &:hover {
    background: var(--color-primary);
    color: var(--color-bg);
  }
`;

const NavLink = styled(RouterLink, {
  shouldForwardProp: prop => prop !== '$active',
})<{ $active?: boolean }>`
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 500;
  text-decoration: none;
  padding: 12px 16px;
  border-radius: 8px;
  transition:
    background 0.2s,
    color 0.2s;
  background: ${({ $active }) => ($active ? 'var(--color-primary)' : 'none')};
  color: ${({ $active }) => ($active ? 'var(--color-bg)' : 'var(--text-secondary)')};
  &:hover {
    background: var(--color-primary);
    color: var(--color-bg);
  }
`;

const NavBar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  // Hide navbar on auth-related pages
  if (
    location.pathname === '/' ||
    location.pathname === '/login-register' ||
    location.pathname === '/forgot-password' ||
    location.pathname === '/reset-password' ||
    location.pathname === '/verify-email' ||
    location.pathname === '/verify-email-sent'
  ) {
    return null;
  }
  return (
    <Navbar>
      <Logo to="/">SmartWalletFX</Logo>
      <NavLinks>
        <NavLink to="/dashboard" $active={location.pathname.startsWith('/dashboard')}>
          Dashboard
        </NavLink>
        <NavLink to="/defi" $active={location.pathname.startsWith('/defi')}>
          DeFi
        </NavLink>
        <NavLink to="/settings" $active={location.pathname.startsWith('/settings')}>
          Settings
        </NavLink>
        <LogoutButton
          onClick={async () => {
            await dispatch(logoutUser());
            navigate('/');
          }}
        >
          Logout
        </LogoutButton>
      </NavLinks>
    </Navbar>
  );
};

export default NavBar;
