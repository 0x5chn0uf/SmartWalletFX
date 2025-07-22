import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';

const moveDots = keyframes`
  0% { background-position: 0 0, 20px 20px; }
  100% { background-position: 40px 40px, 60px 60px; }
`;

const fadeIn = keyframes`
  0% { opacity: 0; transform: translateY(20px); }
  100% { opacity: 1; transform: translateY(0); }
`;

const BgDots = styled('div')`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  background:
    radial-gradient(circle, #4fd1c7 1.5px, transparent 1.5px),
    radial-gradient(circle, #6366f1 1.5px, transparent 1.5px);
  background-size:
    40px 40px,
    80px 80px;
  background-position:
    0 0,
    20px 20px;
  animation: ${moveDots} 8s linear infinite;
  opacity: 0.12;
`;

const BackBtn = styled('button')`
  position: fixed;
  top: 32px;
  left: 32px;
  background: none;
  border: none;
  color: #7b879d;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  z-index: 10;
  text-decoration: underline transparent;
  transition:
    color 0.2s,
    text-decoration 0.2s;
  &:hover {
    color: #475569;
    text-decoration: underline #475569;
  }
  @media (max-width: 480px) {
    top: 8px;
    left: 8px;
  }
`;

const Container = styled('div')`
  min-height: 100vh;
  background: #1a1f2e;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
`;

const GlassCard = styled('div')`
  background: rgba(36, 41, 55, 0.7);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-radius: 24px;
  border: 1.5px solid rgba(255, 255, 255, 0.18);
  padding: 48px 36px 36px 36px;
  width: 475px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: ${fadeIn} 0.7s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 1;
  @media (max-width: 480px) {
    padding: 24px 4px;
    width: 98vw;
  }
`;

const Logo = styled('div')`
  font-size: 36px;
  font-weight: 700;
  color: #4fd1c7;
  margin-bottom: 12px;
  letter-spacing: -0.02em;
  text-shadow: 0 2px 8px rgba(79, 209, 199, 0.2);
`;

const Subtitle = styled('div')`
  font-size: 16px;
  color: #e0e7ef;
  margin-bottom: 32px;
  text-align: center;
  font-weight: 400;
`;

interface AuthLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  backButtonText?: string;
  onBackClick?: () => void;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title = 'SmartWalletFX',
  subtitle = 'Sign in to your account or create a new one to access your financial dashboard.',
  backButtonText = '← Back to Homepage',
  onBackClick,
}) => {
  const navigate = useNavigate();

  const handleBackClick = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      navigate('/');
    }
  };

  useEffect(() => {
    const originalHtmlOverflow = document.documentElement.style.overflow;
    const originalBodyOverflow = document.body.style.overflow;
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
    return () => {
      document.documentElement.style.overflow = originalHtmlOverflow;
      document.body.style.overflow = originalBodyOverflow;
    };
  }, []);

  return (
    <Container>
      <BgDots />
      <BackBtn onClick={handleBackClick}>{backButtonText}</BackBtn>
      <GlassCard>
        <Logo>{title}</Logo>
        <Subtitle>{subtitle}</Subtitle>
        {children}
      </GlassCard>
    </Container>
  );
};

export default AuthLayout;
