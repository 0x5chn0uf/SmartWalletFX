import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store';
import { addNotification } from '../store/notificationSlice';
import { AlertColor } from '@mui/material';

interface NotificationOptions {
  severity?: AlertColor;
  autoHideDuration?: number;
}

const useNotification = () => {
  const dispatch = useDispatch<AppDispatch>();

  const showNotification = (
    message: string,
    options: NotificationOptions = {}
  ) => {
    const { severity = 'info', autoHideDuration = 6000 } = options;
    dispatch(addNotification({ message, severity, autoHideDuration }));
  };

  const showSuccess = (message: string, autoHideDuration?: number) => {
    showNotification(message, { severity: 'success', autoHideDuration });
  };

  const showError = (message: string, autoHideDuration?: number) => {
    showNotification(message, { severity: 'error', autoHideDuration });
  };

  const showWarning = (message: string, autoHideDuration?: number) => {
    showNotification(message, { severity: 'warning', autoHideDuration });
  };

  const showInfo = (message: string, autoHideDuration?: number) => {
    showNotification(message, { severity: 'info', autoHideDuration });
  };

  return {
    showNotification,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };
};

export default useNotification; 