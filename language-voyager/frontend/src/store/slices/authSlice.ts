import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { AuthResponse, LoginRequest, RegisterRequest, UserProfile } from '../../types/api';
import api from '../../services/api';

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  token: localStorage.getItem('token'),
  user: null,
  isLoading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest) => {
    const response = await api.post<AuthResponse>('/auth/token', 
      new URLSearchParams({
        username: credentials.username,
        password: credentials.password,
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    
    const data = response.data;
    localStorage.setItem('token', data.access_token);
    return data;
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (userData: RegisterRequest) => {
    const response = await api.post<AuthResponse>('/auth/register', userData);
    return response.data;
  }
);

export const fetchUserProfile = createAsyncThunk(
  'auth/fetchUserProfile',
  async () => {
    const response = await api.get<UserProfile>('/auth/me');
    return response.data;
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.token = null;
      state.user = null;
      localStorage.removeItem('token');
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action: PayloadAction<AuthResponse>) => {
        state.isLoading = false;
        state.token = action.payload.access_token;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'Login failed';
      })
      // Register
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message ?? 'Registration failed';
      })
      // Fetch Profile
      .addCase(fetchUserProfile.fulfilled, (state, action: PayloadAction<UserProfile>) => {
        state.user = action.payload;
      })
      .addCase(fetchUserProfile.rejected, (state, action) => {
        state.error = action.error.message ?? 'Failed to fetch profile';
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;