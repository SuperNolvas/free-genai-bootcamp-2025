// Authentication types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: UserProfile;
}

export interface UserProfile {
  id: string;
  email: string;
  createdAt: string;
  updatedAt: string;
  isVerified: boolean;
}

// Progress types
export interface Achievement {
  id: string;
  type: string;
  title: string;
  description: string;
  unlocked_at: string;
}

export interface ProgressResponse {
  language: string;
  region: string;
  proficiency_level: number;
  completed_challenges: string[];
  achievements: Achievement[];
  last_activity: string;
}

// Map types
export interface Region {
  id: string;
  name: string;
  local_name: string;
  description: string;
  center_lat: number;
  center_lon: number;
  language: string;
  difficulty_level: number;
  is_available: boolean;
  metadata: Record<string, any>;
}

export interface POI {
  id: string;
  name: string;
  local_name: string;
  type: string;
  lat: number;
  lon: number;
  region_id: string;
  difficulty_level: number;
  available_content: string[];
}

// WebSocket types
export interface LocationConfig {
  highAccuracyMode: boolean;
  timeout: number;
  maximumAge: number;
  minAccuracy: number;
  updateInterval: number;
  minimumDistance: number;
  backgroundMode: boolean;
  powerSaveMode: boolean;
}

export interface LocationCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  timestamp: string;
}

export interface LocationUpdate {
  type: 'location_update';
  status: 'ok';
  latitude: number;
  longitude: number;
  accuracy?: number;
  timestamp: string;
}

// API Response wrapper
export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}
