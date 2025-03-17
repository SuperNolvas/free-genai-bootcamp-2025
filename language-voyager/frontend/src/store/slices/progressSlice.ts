import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Achievement, ProgressResponse } from '../../types/api';

interface ProgressState {
  overallProgress: {
    totalLanguages: number;
    totalRegions: number;
    totalAchievements: number;
    languages: Record<string, number>;
    totalTimeSpent: number;
  };
  regionProgress: ProgressResponse[];
  achievements: Achievement[];
  isLoading: boolean;
  error: string | null;
}

const initialState: ProgressState = {
  overallProgress: {
    totalLanguages: 0,
    totalRegions: 0,
    totalAchievements: 0,
    languages: {},
    totalTimeSpent: 0,
  },
  regionProgress: [],
  achievements: [],
  isLoading: false,
  error: null,
};

export const fetchOverallProgress = createAsyncThunk(
  'progress/fetchOverall',
  async (_, { getState }) => {
    const state = getState() as { auth: { token: string | null } };
    const response = await fetch('http://localhost:8000/api/v1/progress/', {
      headers: {
        'Authorization': `Bearer ${state.auth.token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch progress');
    }
    
    const data = await response.json();
    return data.data;
  }
);

export const fetchRegionProgress = createAsyncThunk(
  'progress/fetchRegion',
  async (regionId: string, { getState }) => {
    const state = getState() as { auth: { token: string | null } };
    const response = await fetch(`http://localhost:8000/api/v1/progress/region/${regionId}`, {
      headers: {
        'Authorization': `Bearer ${state.auth.token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch region progress');
    }
    
    const data = await response.json();
    return data.data;
  }
);

export const completePOIContent = createAsyncThunk(
  'progress/completePOIContent',
  async ({ poiId, contentId, score }: { poiId: string; contentId: string; score: number }, { getState }) => {
    const state = getState() as { auth: { token: string | null } };
    const response = await fetch(`http://localhost:8000/api/v1/progress/poi/${poiId}/complete`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${state.auth.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content_id: contentId,
        score,
      }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to complete POI content');
    }
    
    const data = await response.json();
    return data.data;
  }
);

const progressSlice = createSlice({
  name: 'progress',
  initialState,
  reducers: {
    clearProgressError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Overall Progress
      .addCase(fetchOverallProgress.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchOverallProgress.fulfilled, (state, action) => {
        state.isLoading = false;
        state.overallProgress = {
          totalLanguages: action.payload.total_languages,
          totalRegions: action.payload.total_regions,
          totalAchievements: action.payload.total_achievements,
          languages: action.payload.languages,
          totalTimeSpent: action.payload.total_time_spent,
        };
      })
      .addCase(fetchOverallProgress.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'Failed to fetch overall progress';
      })
      // Fetch Region Progress
      .addCase(fetchRegionProgress.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchRegionProgress.fulfilled, (state, action: PayloadAction<ProgressResponse[]>) => {
        state.isLoading = false;
        state.regionProgress = action.payload;
      })
      .addCase(fetchRegionProgress.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'Failed to fetch region progress';
      })
      // Complete POI Content
      .addCase(completePOIContent.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(completePOIContent.fulfilled, (state, action: PayloadAction<Achievement[]>) => {
        state.isLoading = false;
        // Add new achievements to the list without duplicates
        const currentIds = new Set(state.achievements.map(a => a.id));
        const newAchievements = action.payload.filter(a => !currentIds.has(a.id));
        state.achievements = [...state.achievements, ...newAchievements];
      })
      .addCase(completePOIContent.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'Failed to complete POI content';
      });
  },
});

export const { clearProgressError } = progressSlice.actions;
export default progressSlice.reducer;