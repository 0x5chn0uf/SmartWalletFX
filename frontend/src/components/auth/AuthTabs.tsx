import React from 'react';
import styled from '@emotion/styled';

const TabGroup = styled('div')`
  display: flex;
  margin-bottom: 32px;
  position: relative;
  width: 100%;
`;

const Tab = styled('button')<{ active: boolean }>`
  flex: 1;
  padding: 12px 0;
  background: none;
  border: none;
  color: ${props => (props.active ? '#4fd1c7' : '#9ca3af')};
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.3s;
  outline: none;
  &:hover {
    color: #4fd1c7;
  }
`;

const TabUnderline = styled('div')<{ tab: 'login' | 'register' }>`
  position: absolute;
  bottom: 0;
  left: ${props => (props.tab === 'login' ? '0%' : '50%')};
  width: 50%;
  height: 2px;
  background: linear-gradient(90deg, #4fd1c7 0%, #6366f1 100%);
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 1px;
`;

interface AuthTabsProps {
  activeTab: 'login' | 'register';
  onTabChange: (tab: 'login' | 'register') => void;
}

const AuthTabs: React.FC<AuthTabsProps> = ({ activeTab, onTabChange }) => {
  return (
    <TabGroup>
      <Tab active={activeTab === 'login'} onClick={() => onTabChange('login')}>
        Login
      </Tab>
      <Tab active={activeTab === 'register'} onClick={() => onTabChange('register')}>
        Register
      </Tab>
      <TabUnderline tab={activeTab} />
    </TabGroup>
  );
};

export default AuthTabs;
