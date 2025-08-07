import React from 'react';
import styled from '@emotion/styled';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { logoutUser } from '../store/authSlice';
import { AppDispatch } from '../store';

const Navbar = styled.nav`
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
  margin-left: 0;
  font-weight: 800;
  font-size: 24px;
  letter-spacing: -0.02em;
  text-shadow: 0 2px 8px rgba(79, 209, 199, 0.2);
  &:hover {
    color: #4fd1c7;
    text-decoration: none;
  }
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

  // Special navbar for DeFi pages - show only Register
  if (location.pathname.startsWith('/defi')) {
    const SimpleRegisterLink = styled(RouterLink)`
      color: #9ca3af;
      text-decoration: none;
      font-weight: 600;
      font-size: 16px;
      transition: color 0.2s;
      &:hover {
        color: #4fd1c7;
      }
    `;
    
    return (
      <Navbar>
        <Logo to="/">SmartWalletFX</Logo>
        <NavLinks>
          <SimpleRegisterLink 
            to="/login-register"
            state={{ from: location.pathname }}
          >
            Register
          </SimpleRegisterLink>
        </NavLinks>
      </Navbar>
    );
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
