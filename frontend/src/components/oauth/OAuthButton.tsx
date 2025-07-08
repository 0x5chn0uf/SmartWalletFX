import React from 'react';
import { FaGoogle, FaGithub } from 'react-icons/fa';

interface Props {
  provider: 'google' | 'github';
  onClick?: () => void;
}

const providerLabels: Record<Props['provider'], string> = {
  google: 'Continue with Google',
  github: 'Continue with GitHub',
};

const providerIcons: Record<Props['provider'], JSX.Element> = {
  google: <FaGoogle className="oauth-icon" />,
  github: <FaGithub className="oauth-icon" />,
};

export const OAuthButton: React.FC<Props> = ({ provider, onClick }) => {
  const handleClick = () => {
    if (onClick) onClick();
    window.location.href = `/auth/oauth/${provider}/login`;
  };
  return (
    <button className="oauth-btn" onClick={handleClick} type="button">
      {providerIcons[provider]}
      <span>{providerLabels[provider]}</span>
    </button>
  );
};
