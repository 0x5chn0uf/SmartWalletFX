import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { AppDispatch } from '../../store';
import { login } from '../../store/authSlice';
import { OAuthButton } from '../oauth/OAuthButton';

const fadeIn = keyframes`
  0% { opacity: 0; transform: translateY(20px); }
  100% { opacity: 1; transform: translateY(0); }
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

const ForgotPasswordLink = styled('a')`
  color: #6366f1;
  text-decoration: none;
  font-size: 13px;
  text-align: center;
  display: block;
  margin-top: 8px;
  transition: color 0.2s;
  cursor: pointer;
  &:hover {
    color: #4fd1c7;
  }
`;

const ErrorMessage = styled('div')`
  color: #ff6b6b;
  font-size: 14px;
  text-align: center;
`;

interface LoginFormProps {
  onSwitchToRegister: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSwitchToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await dispatch(login({ email, password })).unwrap();
      navigate('/dashboard');
    } catch (err: any) {
      const status = err?.status ?? err?.response?.status;
      if (!status) {
        setError('Unable to reach server');
      } else if (status === 401) {
        setError('Invalid email or password');
      } else if (status === 403) {
        setError('Account not verified. Check your email for verification link.');
      } else {
        setError('Login failed');
      }
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Label htmlFor="login-email">Email</Label>
      <Input
        type="email"
        id="login-email"
        name="email"
        placeholder="Enter your email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        required
      />
      <Label htmlFor="login-password">Password</Label>
      <Input
        type="password"
        id="login-password"
        name="password"
        placeholder="Enter your password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
      />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <SubmitBtn type="submit">Login</SubmitBtn>
      <ForgotPasswordLink onClick={() => navigate('/forgot-password')}>
        Forgot password?
      </ForgotPasswordLink>
      <OAuthButton provider="google" />
      <OAuthButton provider="github" />
      <SwitchLink onClick={onSwitchToRegister}>Don't have an account? Register</SwitchLink>
    </Form>
  );
};

export default LoginForm;
