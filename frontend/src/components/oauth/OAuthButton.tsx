import React from 'react';

interface Props {
  provider: 'google' | 'github';
  onClick?: () => void;
}

const providerLabels: Record<Props['provider'], string> = {
  google: 'Continue with Google',
  github: 'Continue with GitHub',
};

export const OAuthButton: React.FC<Props> = ({ provider, onClick }) => {
  const handleClick = () => {
    if (onClick) onClick();
    window.location.href = `/auth/oauth/${provider}/login`;
  };
  return (
    <button className="oauth-btn" onClick={handleClick} type="button">
      {providerLabels[provider]}
    </button>
  );
};
