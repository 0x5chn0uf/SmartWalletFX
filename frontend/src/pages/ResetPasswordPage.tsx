import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AppDispatch, RootState } from '../store';
import { resetPassword, verifyResetToken, resetState } from '../store/passwordResetSlice';
import { useAuth } from '../hooks/useAuth';

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

const Label = styled('label')`
  font-size: 14px;
  color: #bfc7d5;
  margin-bottom: 6px;
  font-weight: 500;
`;

const Input = styled('input')`
  padding: 12px;
  border-radius: 10px;
  border: 1.5px solid rgba(255, 255, 255, 0.18);
  background: rgba(45, 53, 72, 0.7);
  color: #fff;
  font-size: 16px;
  outline: none;
  transition:
    border 0.2s,
    box-shadow 0.2s,
    opacity 0.2s;
  box-shadow: 0 1px 4px rgba(79, 209, 199, 0.05);
  opacity: ${props => (props.disabled ? 0.6 : 1)};
  cursor: ${props => (props.disabled ? 'not-allowed' : 'text')};
  &:focus {
    border: 1.5px solid #4fd1c7;
    box-shadow: 0 0 0 2px #4fd1c733;
  }
  &:disabled {
    pointer-events: none;
  }
`;

const SubmitBtn = styled('button')`
  background: linear-gradient(90deg, #4fd1c7 0%, #6366f1 100%);
  color: #1f2937;
  border: none;
  border-radius: 10px;
  padding: 14px 0;
  font-size: 16px;
  font-weight: 700;
  cursor: ${props => (props.disabled ? 'not-allowed' : 'pointer')};
  margin-top: 8px;
  box-shadow: 0 2px 8px rgba(79, 209, 199, 0.15);
  transition:
    transform 0.18s,
    box-shadow 0.18s,
    opacity 0.2s;
  opacity: ${props => (props.disabled ? 0.6 : 1)};
  &:hover {
    transform: ${props => (props.disabled ? 'none' : 'scale(1.04)')};
    box-shadow: ${props =>
      props.disabled
        ? '0 2px 8px rgba(79, 209, 199, 0.15)'
        : '0 4px 16px rgba(99, 102, 241, 0.18)'};
  }
  &:disabled {
    pointer-events: none;
  }
`;

interface MessageProps {
  type: 'success' | 'error';
}

const Message = styled('div')<MessageProps>`
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 500;
  ${props =>
    props.type === 'success' &&
    `
    background: rgba(34, 197, 94, 0.1);
    color: #22c55e;
    border: 1px solid rgba(34, 197, 94, 0.2);
  `}
  ${props =>
    props.type === 'error' &&
    `
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.2);
  `}
`;

const ResetPasswordPage = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [password, setPassword] = useState('');
  const { isAuthenticated } = useAuth();

  const passwordReset = useSelector((state: RootState) => state.passwordReset);
  const isLoading = passwordReset.status === 'loading';
  const isSuccess = passwordReset.status === 'succeeded';
  const isError = passwordReset.status === 'failed';
  const isValidatingToken = passwordReset.tokenValidationStatus === 'loading';
  const isTokenValid = passwordReset.tokenValidationStatus === 'succeeded';
  const tokenValidationError = passwordReset.tokenValidationStatus === 'failed';

  // Redirect authenticated users
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  // Validate token on page load
  useEffect(() => {
    if (token && !isAuthenticated) {
      dispatch(verifyResetToken(token));
    } else if (!token) {
      navigate('/forgot-password');
    }

    // Reset state when component mounts
    return () => {
      dispatch(resetState());
    };
  }, [token, dispatch, navigate, isAuthenticated]);

  // Redirect to login after successful password reset
  useEffect(() => {
    if (isSuccess) {
      setTimeout(() => {
        navigate('/login-register');
      }, 3000);
    }
  }, [isSuccess, navigate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim() || !isTokenValid) return;
    dispatch(resetPassword({ token, password }));
  };

  // Show loading state while validating token
  if (isValidatingToken) {
    return (
      <Container>
        <BgDots />
        <GlassCard>
          <Logo>SmartWalletFX</Logo>
          <Subtitle>Validating reset token...</Subtitle>
        </GlassCard>
      </Container>
    );
  }

  // Show error if token validation failed
  if (tokenValidationError) {
    return (
      <Container>
        <BgDots />
        <BackBtn onClick={() => navigate('/forgot-password')}>← Request New Reset</BackBtn>
        <GlassCard>
          <Logo>SmartWalletFX</Logo>
          <Subtitle>Reset token is invalid or expired.</Subtitle>
          <Message type="error">
            {passwordReset.error ||
              'The password reset link is invalid or has expired. Please request a new one.'}
          </Message>
        </GlassCard>
      </Container>
    );
  }

  // Don't render form if token is not valid
  if (!isTokenValid) {
    return null;
  }

  return (
    <Container>
      <BgDots />
      <BackBtn onClick={() => navigate('/login-register')}>← Back to Login</BackBtn>
      <GlassCard>
        <Logo>SmartWalletFX</Logo>
        <Subtitle>
          {isSuccess ? 'Password reset complete!' : 'Enter a new password to complete the reset.'}
        </Subtitle>

        {isSuccess && (
          <Message type="success">
            Your password has been reset successfully! Redirecting to login...
          </Message>
        )}

        {isError && <Message type="error">{passwordReset.error}</Message>}

        {!isSuccess && (
          <Form onSubmit={handleSubmit}>
            <Label htmlFor="password">New Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              disabled={isLoading}
              required
              minLength={8}
              placeholder="Enter your new password"
            />
            <SubmitBtn
              type="submit"
              disabled={isLoading || !password.trim() || password.length < 8}
            >
              {isLoading ? 'Resetting...' : 'Reset Password'}
            </SubmitBtn>
          </Form>
        )}
      </GlassCard>
    </Container>
  );
};

export default ResetPasswordPage;
