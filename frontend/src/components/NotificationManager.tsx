import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '../store';
import { removeNotification } from '../store/notificationSlice';
import Toast from './Toast';

const NotificationManager: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const notifications = useSelector((state: RootState) => state.notification.notifications);

  const handleClose = (id: string) => {
    dispatch(removeNotification(id));
  };

  return (
    <>
      {notifications.map((notification) => (
        <Toast
          key={notification.id}
          open={true}
          message={notification.message}
          severity={notification.severity}
          onClose={() => handleClose(notification.id)}
          autoHideDuration={notification.autoHideDuration}
        />
      ))}
    </>
  );
};

export default NotificationManager; 