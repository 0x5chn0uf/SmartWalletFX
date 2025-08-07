import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import AuthLayout from '../components/auth/AuthLayout';
import AuthTabs from '../components/auth/AuthTabs';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';

const LoginRegisterPage: React.FC = () => {
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, status } = useAuth();

  const handleTab = (newTab: 'login' | 'register') => {
    setTab(newTab);
  };

  useEffect(() => {
    if (isAuthenticated && status === 'succeeded') {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, status, navigate]);

  // Determine back button text and behavior based on where user came from
  const getBackButtonConfig = () => {
    const referrer = location.state?.from || document.referrer;
    
    // Check if coming from DeFi page
    if (referrer && referrer.includes('/defi')) {
      return {
        text: '← Back to Wallet Preview',
        onClick: () => navigate(-1)
      };
    }
    
    // Check if there's a previous page in history (not direct URL entry)
    if (location.state?.from || (document.referrer && document.referrer !== window.location.href)) {
      return {
        text: '← Back',
        onClick: () => navigate(-1)
      };
    }
    
    // Default to homepage
    return {
      text: '← Back to Homepage',
      onClick: () => navigate('/')
    };
  };

  const backConfig = getBackButtonConfig();

  // Show nothing while redirecting authenticated users
  if (isAuthenticated && status === 'succeeded') {
    return null;
  }

  return (
    <AuthLayout 
      backButtonText={backConfig.text}
      onBackClick={backConfig.onClick}
    >
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
