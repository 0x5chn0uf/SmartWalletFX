import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { AppDispatch } from '../../store';
import { registerUser } from '../../store/authSlice';
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
  font-size: 12px;
  font-weight: 400;
  transition:
    opacity 0.3s,
    visibility 0.3s;
  &::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: #374151 transparent transparent transparent;
  }
`;

const ErrorMessage = styled('div')`
  color: #ff6b6b;
  font-size: 14px;
  text-align: center;
`;

interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setError('');
    try {
      await dispatch(registerUser({ email, password })).unwrap();
      navigate('/verify-email-sent');
    } catch (err: any) {
      const status = err?.status ?? err?.response?.status;
      if (!status) {
        setError('Unable to reach server');
      } else if (status === 400) {
        setError('Password does not meet strength requirements');
      } else if (status === 409) {
        setError('Email already registered');
      } else {
        setError('Registration failed');
      }
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Label htmlFor="register-email">Email</Label>
      <Input
        type="email"
        id="register-email"
        name="email"
        placeholder="Enter your email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        required
      />
      <Label htmlFor="register-password">
        Password
        <InfoIcon aria-label="password requirements">
          ⓘ<Tooltip>Password must be at least 8 characters and include a number and symbol</Tooltip>
        </InfoIcon>
      </Label>
      <Input
        type="password"
        id="register-password"
        name="password"
        placeholder="Create a password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
      />
      <Label htmlFor="register-confirm">Confirm Password</Label>
      <Input
        type="password"
        id="register-confirm"
        name="confirm"
        placeholder="Confirm your password"
        value={confirmPassword}
        onChange={e => setConfirmPassword(e.target.value)}
        required
      />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <SubmitBtn type="submit">Register</SubmitBtn>
      <OAuthButton provider="google" />
      <OAuthButton provider="github" />
      <SwitchLink onClick={onSwitchToLogin}>Already have an account? Login</SwitchLink>
    </Form>
  );
};

export default RegisterForm;
