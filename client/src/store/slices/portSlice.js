import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

export const fetchPorts = createAsyncThunk(
  'ports/fetchPorts',
  async (filters = {}) => {
    const response = await api.get('/ports', { params: filters });
    return response.data;
  }
);

export const fetchPortDetails = createAsyncThunk(
  'ports/fetchPortDetails',
  async (id) => {
    const response = await api.get(`/ports/${id}`);
    return response.data.port;
  }
);

const portSlice = createSlice({
  name: 'ports',
  initialState: {
    list: [],
    currentPort: null,
    loading: false,
    error: null,
  },
  reducers: {
    updatePortCongestion: (state, action) => {
      const { portId, congestion } = action.payload;
      const port = state.list.find(p => p._id === portId);
      if (port) {
        port.currentCongestion = congestion;
      }
      if (state.currentPort?._id === portId) {
        state.currentPort.currentCongestion = congestion;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPorts.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchPorts.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload.ports;
      })
      .addCase(fetchPorts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(fetchPortDetails.fulfilled, (state, action) => {
        state.currentPort = action.payload;
      });
  },
});

export const { updatePortCongestion } = portSlice.actions;
export default portSlice.reducer;
