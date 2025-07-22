import React from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AppDispatch } from '../store';
import { verifyEmail } from '../store/emailVerificationSlice';
import { RootState } from '../store';

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

const Form = styled('form')`
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 18px;
  animation: ${fadeIn} 0.5s cubic-bezier(0.4, 0, 0.2, 1);
`;

const SubmitBtn = styled('button')`
  background: linear-gradient(90deg, #4fd1c7 0%, #6366f1 100%);
  color: #1f2937;
  border: none;
  border-radius: 10px;
  padding: 14px 0;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  margin-top: 8px;
  box-shadow: 0 2px 8px rgba(79, 209, 199, 0.15);
  transition:
    transform 0.18s,
    box-shadow 0.18s;
  &:hover {
    transform: scale(1.04);
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.18);
  }
`;

const EmailVerificationPage = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const verificationStatus = useSelector((state: RootState) => state.emailVerification.status);

  React.useEffect(() => {
    if (token) {
      // Trigger verification automatically on mount
      dispatch(verifyEmail(token));
    }
  }, [token, dispatch]);

  return (
    <Container>
      <BgDots />
      <BackBtn onClick={() => navigate('/login-register')}>← Back to Login</BackBtn>
      <GlassCard>
        <Logo>SmartWalletFX</Logo>
        {verificationStatus === 'loading' && (
          <Subtitle>Verifying your email, please wait…</Subtitle>
        )}
        {verificationStatus === 'succeeded' && (
          <Subtitle>Your email has been verified successfully!</Subtitle>
        )}
        {verificationStatus === 'failed' && (
          <Subtitle>Verification failed. Please try again.</Subtitle>
        )}

        <Form
          onSubmit={e => {
            e.preventDefault();
            navigate('/dashboard');
          }}
        >
          <SubmitBtn type="submit">Go to Dashboard</SubmitBtn>
        </Form>
      </GlassCard>
    </Container>
  );
};

export default EmailVerificationPage;
