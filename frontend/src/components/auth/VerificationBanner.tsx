import React from 'react';
import { Alert, Button } from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store';
import { resendVerification } from '../../store/emailVerificationSlice';

const VerificationBanner: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const user = useSelector((state: RootState) => state.auth.user);

  if (!user || user.email_verified) {
    return null;
  }

  const handleResend = () => {
    dispatch(resendVerification(user.email));
  };

  return (
    <Alert
      severity="warning"
      action={
        <Button color="inherit" size="small" onClick={handleResend}>
          Resend
        </Button>
      }
      sx={{ mb: 2 }}
    >
      Please verify your email address to unlock all features.
    </Alert>
  );
};

export default VerificationBanner;
