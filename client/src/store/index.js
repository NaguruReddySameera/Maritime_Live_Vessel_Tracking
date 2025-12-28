import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import vesselReducer from './slices/vesselSlice';
import portReducer from './slices/portSlice';
import safetyReducer from './slices/safetySlice';
import alertReducer from './slices/alertSlice';
import dashboardReducer from './slices/dashboardSlice';

const store = configureStore({
  reducer: {
    auth: authReducer,
    vessels: vesselReducer,
    ports: portReducer,
    safety: safetyReducer,
    alerts: alertReducer,
    dashboards: dashboardReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export default store;
