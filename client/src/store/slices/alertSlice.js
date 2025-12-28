import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

export const fetchAlerts = createAsyncThunk(
  'alerts/fetchAlerts',
  async (filters = {}) => {
    const response = await api.get('/safety/alerts', { params: filters });
    return response.data;
  }
);

const alertSlice = createSlice({
  name: 'alerts',
  initialState: {
    list: [],
    unreadCount: 0,
    loading: false,
  },
  reducers: {
    addAlert: (state, action) => {
      state.list.unshift(action.payload);
      state.unreadCount += 1;
    },
    markAsRead: (state, action) => {
      const alert = state.list.find(a => a._id === action.payload);
      if (alert && !alert.read) {
        alert.read = true;
        state.unreadCount -= 1;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAlerts.fulfilled, (state, action) => {
        state.list = action.payload.alerts;
        state.unreadCount = action.payload.alerts.filter(a => !a.read).length;
      });
  },
});

export const { addAlert, markAsRead } = alertSlice.actions;
export default alertSlice.reducer;
