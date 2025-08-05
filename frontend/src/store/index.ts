import { configureStore } from '@reduxjs/toolkit';
import authSlice from './authSlice';
import inmatesSlice from './inmatesSlice';
import monitorsSlice from './monitorsSlice';
import jailsSlice from './jailsSlice';
import usersSlice from './usersSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    inmates: inmatesSlice,
    monitors: monitorsSlice,
    jails: jailsSlice,
    users: usersSlice,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
