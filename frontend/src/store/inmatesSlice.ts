import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Inmate, InmateSearchParams, PaginatedResponse } from '../types';
import { apiService } from '../services/api';

interface InmatesState {
  inmates: Inmate[];
  currentInmate: Inmate | null;
  loading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
}

const initialState: InmatesState = {
  inmates: [],
  currentInmate: null,
  loading: false,
  error: null,
  totalCount: 0,
  currentPage: 1,
};

export const fetchInmates = createAsyncThunk(
  'inmates/fetchInmates',
  async (params?: InmateSearchParams) => {
    const response = await apiService.getInmates(params);
    return response;
  }
);

export const fetchInmate = createAsyncThunk(
  'inmates/fetchInmate',
  async (id: number) => {
    const response = await apiService.getInmate(id);
    return response;
  }
);

const inmatesSlice = createSlice({
  name: 'inmates',
  initialState,
  reducers: {
    clearCurrentInmate: (state) => {
      state.currentInmate = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInmates.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchInmates.fulfilled, (state, action) => {
        state.loading = false;
        state.inmates = action.payload.items;
        state.totalCount = action.payload.total;
        state.currentPage = action.payload.page;
      })
      .addCase(fetchInmates.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch inmates';
      })
      .addCase(fetchInmate.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchInmate.fulfilled, (state, action) => {
        state.loading = false;
        state.currentInmate = action.payload;
      })
      .addCase(fetchInmate.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch inmate';
      });
  },
});

export const { clearCurrentInmate, clearError } = inmatesSlice.actions;
export default inmatesSlice.reducer;
