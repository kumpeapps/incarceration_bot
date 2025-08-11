import { createSlice } from '@reduxjs/toolkit';
import { Jail } from '../types';

interface JailsState {
  jails: Jail[];
  loading: boolean;
  error: string | null;
}

const initialState: JailsState = {
  jails: [],
  loading: false,
  error: null,
};

const jailsSlice = createSlice({
  name: 'jails',
  initialState,
  reducers: {},
});

export default jailsSlice.reducer;
