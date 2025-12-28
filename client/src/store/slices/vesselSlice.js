import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

export const fetchVessels = createAsyncThunk(
  'vessels/fetchVessels',
  async (filters = {}) => {
    const response = await api.get('/vessels', { params: filters });
    return response.data;
  }
);

export const fetchVesselDetails = createAsyncThunk(
  'vessels/fetchVesselDetails',
  async (id) => {
    const response = await api.get(`/vessels/${id}`);
    return response.data.vessel;
  }
);

export const addVesselNote = createAsyncThunk(
  'vessels/addNote',
  async ({ id, note }) => {
    const response = await api.post(`/vessels/${id}/notes`, { note });
    return response.data;
  }
);

const vesselSlice = createSlice({
  name: 'vessels',
  initialState: {
    list: [],
    currentVessel: null,
    loading: false,
    error: null,
    totalPages: 1,
    currentPage: 1,
  },
  reducers: {
    updateVesselPosition: (state, action) => {
      const { vesselId, position } = action.payload;
      const vessel = state.list.find(v => v._id === vesselId);
      if (vessel) {
        vessel.currentPosition = position;
      }
      if (state.currentVessel?._id === vesselId) {
        state.currentVessel.currentPosition = position;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchVessels.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchVessels.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload.vessels;
        state.totalPages = action.payload.totalPages;
        state.currentPage = action.payload.currentPage;
      })
      .addCase(fetchVessels.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(fetchVesselDetails.fulfilled, (state, action) => {
        state.currentVessel = action.payload;
      });
  },
});

export const { updateVesselPosition } = vesselSlice.actions;
export default vesselSlice.reducer;
