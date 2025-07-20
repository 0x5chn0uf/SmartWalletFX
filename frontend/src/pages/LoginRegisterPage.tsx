import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import AuthLayout from '../components/auth/AuthLayout';
import AuthTabs from '../components/auth/AuthTabs';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';

const LoginRegisterPage: React.FC = () => {
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const navigate = useNavigate();
  const { isAuthenticated, status } = useAuth();

  const handleTab = (newTab: 'login' | 'register') => {
    setTab(newTab);
  };

  useEffect(() => {
    if (isAuthenticated && status === 'succeeded') {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, status, navigate]);

  // Show nothing while redirecting authenticated users
  if (isAuthenticated && status === 'succeeded') {
    return null;
  }

  return (
    <AuthLayout>
      <AuthTabs activeTab={tab} onTabChange={handleTab} />
      {tab === 'login' ? (
        <LoginForm onSwitchToRegister={() => handleTab('register')} />
      ) : (
        <RegisterForm onSwitchToLogin={() => handleTab('login')} />
      )}
    </AuthLayout>
  );
};

export default LoginRegisterPage;
