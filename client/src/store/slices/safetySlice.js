import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

export const fetchSafetyZones = createAsyncThunk(
  'safety/fetchZones',
  async (type) => {
    const response = await api.get(`/safety/${type}`);
    return { type, data: response.data };
  }
);

const safetySlice = createSlice({
  name: 'safety',
  initialState: {
    piracyZones: [],
    weatherZones: [],
    incidents: [],
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchSafetyZones.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchSafetyZones.fulfilled, (state, action) => {
        state.loading = false;
        const { type, data } = action.payload;
        if (type === 'piracy') state.piracyZones = data.zones || [];
        if (type === 'weather') state.weatherZones = data.zones || [];
        if (type === 'incidents') state.incidents = data.incidents || [];
      })
      .addCase(fetchSafetyZones.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export default safetySlice.reducer;
