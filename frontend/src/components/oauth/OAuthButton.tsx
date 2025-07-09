import React from 'react';
import { FcGoogle } from 'react-icons/fc';
import { FaGithub } from 'react-icons/fa';

interface Props {
  provider: 'google' | 'github';
  onClick?: () => void;
}

const providerLabels: Record<Props['provider'], string> = {
  google: 'Continue with Google',
  github: 'Continue with GitHub',
};

const providerIcons: Record<Props['provider'], React.ReactElement> = {
  google: <FcGoogle className="oauth-icon" />,
  github: <FaGithub className="oauth-icon" />,
};

// Resolve backend API base URL from Vite env variable (defined in services/api.ts as well)
// Fallback to localhost:8000 in dev if not provided.
const API_URL = (import.meta as any).env.VITE_API_URL || 'http://localhost:8000';

export const OAuthButton: React.FC<Props> = ({ provider, onClick }) => {
  const handleClick = () => {
    if (onClick) onClick();
    // Redirect to backend OAuth login endpoint (e.g., http://localhost:8000/auth/oauth/github/login)
    window.location.href = `${API_URL}/auth/oauth/${provider}/login`;
  };
  return (
    <button className={'oauth-btn oauth-btn-' + provider} onClick={handleClick} type="button">
      {providerIcons[provider]}
      <span>{providerLabels[provider]}</span>
    </button>
  );
};
