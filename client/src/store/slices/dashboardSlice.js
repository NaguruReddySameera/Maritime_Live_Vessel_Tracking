import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

export const fetchDashboards = createAsyncThunk(
  'dashboards/fetchDashboards',
  async () => {
    const response = await api.get('/dashboards');
    return response.data;
  }
);

export const createDashboard = createAsyncThunk(
  'dashboards/create',
  async (data) => {
    const response = await api.post('/dashboards', data);
    return response.data.dashboard;
  }
);

const dashboardSlice = createSlice({
  name: 'dashboards',
  initialState: {
    list: [],
    currentDashboard: null,
    loading: false,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboards.fulfilled, (state, action) => {
        state.list = action.payload.dashboards;
      })
      .addCase(createDashboard.fulfilled, (state, action) => {
        state.list.push(action.payload);
      });
  },
});

export default dashboardSlice.reducer;
