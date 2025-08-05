import { createSlice } from '@reduxjs/toolkit';
import { Monitor } from '../types';

interface MonitorsState {
  monitors: Monitor[];
  loading: boolean;
  error: string | null;
}

const initialState: MonitorsState = {
  monitors: [],
  loading: false,
  error: null,
};

const monitorsSlice = createSlice({
  name: 'monitors',
  initialState,
  reducers: {},
});

export default monitorsSlice.reducer;
