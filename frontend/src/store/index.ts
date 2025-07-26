import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import dashboardReducer from './dashboardSlice';
import walletsReducer from './walletsSlice';
import walletDetailReducer from './walletDetailSlice';
import notificationReducer from './notificationSlice';
import passwordResetReducer from './passwordResetSlice';
import emailVerificationReducer from './emailVerificationSlice';
import userProfileReducer from './slices/userProfileSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    dashboard: dashboardReducer,
    wallets: walletsReducer,
    walletDetail: walletDetailReducer,
    notification: notificationReducer,
    passwordReset: passwordResetReducer,
    emailVerification: emailVerificationReducer,
    userProfile: userProfileReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
