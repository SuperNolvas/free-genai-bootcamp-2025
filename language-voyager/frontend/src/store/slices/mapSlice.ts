import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Region, POI, LocationConfig, LocationUpdate } from '../../types/api';

interface MapState {
  currentRegion: Region | null;
  availableRegions: Region[];
  nearbyPOIs: POI[];
  currentLocation: {
    latitude: number;
    longitude: number;
    accuracy?: number;
  } | null;
  locationConfig: LocationConfig;
  isLoading: boolean;
  error: string | null;
  webSocketConnected: boolean;
}

const initialState: MapState = {
  currentRegion: null,
  availableRegions: [],
  nearbyPOIs: [],
  currentLocation: null,
  locationConfig: {
    highAccuracyMode: true,
    timeout: 10000,
    maximumAge: 30000,
    minAccuracy: 20.0,
    updateInterval: 5.0,
    minimumDistance: 10.0,
    backgroundMode: false,
    powerSaveMode: false,
  },
  isLoading: false,
  error: null,
  webSocketConnected: false,
};

export const fetchRegions = createAsyncThunk(
  'map/fetchRegions',
  async (_, { getState }) => {
    const state = getState() as { auth: { token: string | null } };
    const response = await fetch('http://localhost:8000/api/v1/map/regions', {
      headers: {
        'Authorization': `Bearer ${state.auth.token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch regions');
    }
    
    const data = await response.json();
    return data.data;
  }
);

export const fetchNearbyPOIs = createAsyncThunk(
  'map/fetchNearbyPOIs',
  async ({ lat, lon }: { lat: number; lon: number }, { getState }) => {
    const state = getState() as { auth: { token: string | null } };
    const response = await fetch(
      `http://localhost:8000/api/v1/map/pois/nearby?lat=${lat}&lon=${lon}`,
      {
        headers: {
          'Authorization': `Bearer ${state.auth.token}`,
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch nearby POIs');
    }
    
    const data = await response.json();
    return data.data;
  }
);

const mapSlice = createSlice({
  name: 'map',
  initialState,
  reducers: {
    setCurrentLocation: (state, action: PayloadAction<LocationUpdate>) => {
      state.currentLocation = action.payload.coords;
    },
    updateLocationConfig: (state, action: PayloadAction<Partial<LocationConfig>>) => {
      state.locationConfig = { ...state.locationConfig, ...action.payload };
    },
    setWebSocketConnected: (state, action: PayloadAction<boolean>) => {
      state.webSocketConnected = action.payload;
    },
    setCurrentRegion: (state, action: PayloadAction<Region>) => {
      state.currentRegion = action.payload;
    },
    clearMapError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Regions
      .addCase(fetchRegions.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchRegions.fulfilled, (state, action: PayloadAction<Region[]>) => {
        state.isLoading = false;
        state.availableRegions = action.payload;
      })
      .addCase(fetchRegions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'Failed to fetch regions';
      })
      // Fetch Nearby POIs
      .addCase(fetchNearbyPOIs.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchNearbyPOIs.fulfilled, (state, action: PayloadAction<POI[]>) => {
        state.isLoading = false;
        state.nearbyPOIs = action.payload;
      })
      .addCase(fetchNearbyPOIs.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'Failed to fetch nearby POIs';
      });
  },
});

export const {
  setCurrentLocation,
  updateLocationConfig,
  setWebSocketConnected,
  setCurrentRegion,
  clearMapError,
} = mapSlice.actions;

export default mapSlice.reducer;