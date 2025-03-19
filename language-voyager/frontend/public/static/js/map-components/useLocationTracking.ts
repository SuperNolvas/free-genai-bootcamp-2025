import { useEffect, useState, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { LocationConfig, LocationUpdate } from '@/types/api';
import { updateLocationConfig } from '@/store/slices/mapSlice';
import { webSocketService } from '@/services';

export function useLocationTracking() {
  const dispatch = useDispatch();
  const { currentLocation, locationConfig, isWebSocketConnected } = useSelector((state: RootState) => state.map);
  const [permissionStatus, setPermissionStatus] = useState<PermissionState>('prompt');
  const [isTracking, setIsTracking] = useState(false);

  useEffect(() => {
    if ('permissions' in navigator) {
      navigator.permissions.query({ name: 'geolocation' })
        .then(status => {
          setPermissionStatus(status.state);
          status.onchange = () => setPermissionStatus(status.state);
        });
    }
  }, []);

  const startTracking = useCallback(() => {
    webSocketService.connect();
    setIsTracking(true);
  }, []);

  const stopTracking = useCallback(() => {
    webSocketService.disconnect();
    setIsTracking(false);
  }, []);

  const updateConfig = useCallback((config: Partial<LocationConfig>) => {
    dispatch(updateLocationConfig(config));
    webSocketService.updateConfig(config);
  }, [dispatch]);

  return {
    isConnected: isWebSocketConnected,
    currentLocation,
    locationConfig,
    permissionStatus,
    isTracking,
    startTracking,
    stopTracking,
    updateConfig
  };
}