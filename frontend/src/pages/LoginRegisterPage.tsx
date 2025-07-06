import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { keyframes, css } from '@emotion/react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store';
import { login, registerUser } from '../store/authSlice';

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

const TabGroup = styled('div')`
  display: flex;
  width: 100%;
  margin-bottom: 32px;
  background: transparent;
  border-radius: 8px;
  position: relative;
  overflow: visible;
`;

const Tab = styled('button')<{ active: boolean }>`
  flex: 1;
  padding: 14px 0;
  text-align: center;
  font-weight: 600;
  color: ${props => (props.active ? '#4fd1c7' : '#9ca3af')};
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  position: relative;
  z-index: 1;
  transition: color 0.2s;
`;

const TabUnderline = styled('div')<{ tab: 'login' | 'register' }>`
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  width: 50%;
  background: linear-gradient(90deg, #4fd1c7 0%, #6366f1 100%);
  border-radius: 2px 2px 0 0;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
  transform: ${props => (props.tab === 'login' ? 'translateX(0%)' : 'translateX(100%)')};
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
    box-shadow 0.2s;
  box-shadow: 0 1px 4px rgba(79, 209, 199, 0.05);
  &:focus {
    border: 1.5px solid #4fd1c7;
    box-shadow: 0 0 0 2px #4fd1c733;
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

const SwitchLink = styled('a')`
  color: #6366f1;
  text-decoration: none;
  font-size: 14px;
  margin-top: 12px;
  text-align: center;
  display: block;
  transition: color 0.2s;
  cursor: pointer;
  &:hover {
    color: #4fd1c7;
  }
`;

const InfoIcon = styled('span')`
  margin-left: 6px;
  color: #9ca3af;
  cursor: pointer;
  position: relative;
  display: inline-block;
  font-weight: 700;
  &:hover span {
    visibility: visible;
    opacity: 1;
  }
`;

const Tooltip = styled('span')`
  visibility: hidden;
  opacity: 0;
  width: 220px;
  background: #374151;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 6px 8px;
  position: absolute;
  z-index: 20;
  bottom: 125%;
  left: 50%;
  transform: translateX(-50%);
  transition: opacity 0.2s;
  font-size: 12px;
  line-height: 1.3;
`;

const LoginRegisterPage: React.FC = () => {
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [registerConfirm, setRegisterConfirm] = useState('');
  const [registerError, setRegisterError] = useState('');
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();

  const handleTab = (t: 'login' | 'register') => {
    setTab(t);
    setRegisterError('');
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await dispatch(login({ email: loginEmail, password: loginPassword })).unwrap();
      navigate('/defi');
    } catch (err: any) {
      if (!err.response) {
        setRegisterError('Unable to reach server');
      } else if (err.response.status === 401) {
        setRegisterError('Invalid email or password');
      } else {
        setRegisterError('Login failed');
      }
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (registerPassword !== registerConfirm) {
      setRegisterError('Passwords do not match');
      return;
    }
    setRegisterError('');
    try {
      await dispatch(registerUser({ email: registerEmail, password: registerPassword })).unwrap();
      navigate('/defi');
    } catch (err: any) {
      if (!err.response) {
        setRegisterError('Unable to reach server');
      } else if (err.response.status === 400) {
        setRegisterError('Password does not meet strength requirements');
      } else if (err.response.status === 409) {
        setRegisterError('Email already registered');
      } else {
        setRegisterError('Registration failed');
      }
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
      <BackBtn onClick={() => navigate('/')}>← Back to Homepage</BackBtn>
      <GlassCard>
        <Logo>SmartWalletFX</Logo>
        <Subtitle>
          Sign in to your account or create a new one to access your financial dashboard.
        </Subtitle>
        <TabGroup>
          <Tab active={tab === 'login'} onClick={() => handleTab('login')}>
            Login
          </Tab>
          <Tab active={tab === 'register'} onClick={() => handleTab('register')}>
            Register
          </Tab>
          <TabUnderline tab={tab} />
        </TabGroup>
        {tab === 'login' ? (
          <Form onSubmit={handleLogin}>
            <Label htmlFor="login-email">Email</Label>
            <Input
              type="email"
              id="login-email"
              name="email"
              placeholder="Enter your email"
              value={loginEmail}
              onChange={e => setLoginEmail(e.target.value)}
              required
            />
            <Label htmlFor="login-password">Password</Label>
            <Input
              type="password"
              id="login-password"
              name="password"
              placeholder="Enter your password"
              value={loginPassword}
              onChange={e => setLoginPassword(e.target.value)}
              required
            />
            {registerError && (
              <div style={{ color: '#ff6b6b', fontSize: 14, textAlign: 'center' }}>
                {registerError}
              </div>
            )}
            <SubmitBtn type="submit">Login</SubmitBtn>
            <SwitchLink onClick={() => handleTab('register')}>
              Don't have an account? Register
            </SwitchLink>
          </Form>
        ) : (
          <Form onSubmit={handleRegister}>
            <Label htmlFor="register-email">Email</Label>
            <Input
              type="email"
              id="register-email"
              name="email"
              placeholder="Enter your email"
              value={registerEmail}
              onChange={e => setRegisterEmail(e.target.value)}
              required
            />
            <Label htmlFor="register-password">
              Password
              <InfoIcon aria-label="password requirements">
                ⓘ
                <Tooltip>
                  Password must be at least 8 characters and include a number and symbol
                </Tooltip>
              </InfoIcon>
            </Label>
            <Input
              type="password"
              id="register-password"
              name="password"
              placeholder="Create a password"
              value={registerPassword}
              onChange={e => setRegisterPassword(e.target.value)}
              required
            />
            <Label htmlFor="register-confirm">Confirm Password</Label>
            <Input
              type="password"
              id="register-confirm"
              name="confirm"
              placeholder="Confirm your password"
              value={registerConfirm}
              onChange={e => setRegisterConfirm(e.target.value)}
              required
            />
            {registerError && (
              <div style={{ color: '#ff6b6b', fontSize: 14, textAlign: 'center' }}>
                {registerError}
              </div>
            )}
            <SubmitBtn type="submit">Register</SubmitBtn>
            <SwitchLink onClick={() => handleTab('login')}>
              Already have an account? Login
            </SwitchLink>
          </Form>
        )}
      </GlassCard>
    </Container>
  );
};

export default LoginRegisterPage;
