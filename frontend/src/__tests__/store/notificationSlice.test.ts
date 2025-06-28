import notificationReducer, {
  addNotification,
  removeNotification,
} from '../../store/notificationSlice';
import type { AlertColor } from '@mui/material';

// Inline Notification types for test
interface Notification {
  id: string;
  message: string;
  severity: AlertColor;
  autoHideDuration?: number;
}
interface NotificationState {
  notifications: Notification[];
}

describe('notificationSlice', () => {
  it('should return the initial state', () => {
    expect(notificationReducer(undefined, { type: undefined })).toEqual({
      notifications: [],
    });
  });

  it('should handle addNotification', () => {
    const prevState: NotificationState = { notifications: [] };
    const notification: Omit<Notification, 'id'> = { message: 'Test', severity: 'info' };
    const nextState = notificationReducer(prevState, addNotification(notification));
    expect(nextState.notifications.length).toBe(1);
    expect(nextState.notifications[0].message).toBe('Test');
    expect(nextState.notifications[0].severity).toBe('info');
  });

  it('should handle removeNotification', () => {
    const prevState: NotificationState = {
      notifications: [{ id: '1', message: 'Test', severity: 'info' }],
    };
    expect(notificationReducer(prevState, removeNotification('1'))).toEqual({
      notifications: [],
    });
  });
});
