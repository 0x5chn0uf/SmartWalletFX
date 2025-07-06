import React, { useCallback, useState } from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { useNavigate } from 'react-router-dom';
import { isValidAddress } from '../utils/wallet';

// Shake animation for invalid input
const shake = keyframes`
  0% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  50% { transform: translateX(4px); }
  75% { transform: translateX(-4px); }
  100% { transform: translateX(0); }
`;

const Card = styled.div`
  width: calc(100% - 2rem);
  max-width: 720px;
  margin: 0 auto 48px;
  padding: 32px 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  gap: 16px;

  @media (max-width: 768px) {
    width: calc(100% - 2rem);
    padding: 24px 16px;
  }
`;

const Label = styled.label`
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #e0e7ef;
`;

// Container to align input and CTA horizontally (stack on small screens)
const FieldRow = styled.div`
  display: flex;
  gap: 16px;
  width: 100%;
  align-items: flex-end;

  @media (max-width: 500px) {
    flex-direction: column;
    gap: 12px;
  }
`;

const InputWrapper = styled.div<{ invalid: boolean }>`
  position: relative;
  width: 100%;
  animation: ${({ invalid }) => (invalid ? `${shake} 0.6s` : 'none')};
`;

const Input = styled.input<{ invalid: boolean }>`
  width: 100%;
  height: 48px;
  padding: 0 48px 0 16px;
  border-radius: 16px;
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 14px;
  outline: none;
  transition:
    box-shadow 0.2s,
    border 0.2s;

  &::placeholder {
    color: #9ca3af;
  }

  ${({ invalid }) => invalid && 'border-color: #ef4444;'}

  &:hover {
    border-color: #14b8a6;
  }

  &:focus {
    border-color: transparent;
    box-shadow:
      0 0 0 1.5px #14b8a6,
      0 0 0 3px rgba(99, 102, 241, 0.5);
    /* fallback for browsers without gradient support */
    /* Gradient focus ring */
    box-shadow:
      0 0 0 2px #fff,
      0 0 0 4px linear-gradient(90deg, #14b8a6 0%, #6366f1 100%);
  }
`;

const PasteButton = styled.button`
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #14b8a6;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 0;

  &:hover {
    opacity: 0.8;
  }
`;

const HelperText = styled.span`
  font-size: 10px;
  color: #9ca3af;
  min-height: 14px; /* reserve space */
`;

const ErrorText = styled.span`
  font-size: 10px;
  color: #ef4444;
  min-height: 14px;
`;

const CTAButton = styled.button`
  background: linear-gradient(90deg, #4fd1c7 0%, #6366f1 100%);
  color: #ffffff;
  border: none;
  border-radius: 10px;
  padding: 14px 24px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(79, 209, 199, 0.15);
  transition:
    transform 0.18s,
    box-shadow 0.18s;
  height: 48px;
  text-decoration: none;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.85;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.18);
  }
  &:focus {
    outline: 2px solid #14b8a6;
    outline-offset: 2px;
  }
`;

type WalletPreviewProps = {
  onInputFocus?: () => void;
  onInputBlur?: () => void;
};

const WalletPreview: React.FC<WalletPreviewProps> = ({ onInputFocus, onInputBlur }) => {
  const [value, setValue] = useState('');
  const [invalid, setInvalid] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setValue(text);
    } catch {
      // ignore clipboard errors
    }
  };

  const handleSubmit = useCallback(() => {
    if (!isValidAddress(value)) {
      setInvalid(true);
      setError('Address invalid');
      setTimeout(() => {
        setInvalid(false);
      }, 600);
      return;
    }
    navigate(`/defi/${value}`);
  }, [navigate, value]);

  const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = e => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <Card>
      <Label htmlFor="wallet-input">Track any wallet instantly</Label>
      <FieldRow>
        <InputWrapper invalid={invalid} style={{ flex: 1 }}>
          <Input
            id="wallet-input"
            type="text"
            placeholder="0x742d... or vitalik.eth"
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            invalid={invalid}
            aria-invalid={invalid}
            onFocus={onInputFocus}
            onBlur={onInputBlur}
          />
          <PasteButton type="button" onClick={handlePaste}>
            Paste
          </PasteButton>
        </InputWrapper>
        <CTAButton type="button" onClick={handleSubmit}>
          View Dashboard
        </CTAButton>
      </FieldRow>
      {invalid ? (
        <ErrorText role="alert" aria-live="polite">
          {error}
        </ErrorText>
      ) : (
        <HelperText aria-live="polite">Paste a public address or ENS – no keys needed.</HelperText>
      )}
    </Card>
  );
};

export default WalletPreview;
