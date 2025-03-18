import { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { LocationConfig } from '@/types/api';
import webSocketService from '@/services/websocket';
import { useWebSocket } from '@/context/WebSocketContext';

export function useLocationTracking() {
  const { isConnected } = useWebSocket();
  const location = useSelector((state: RootState) => state.map.currentLocation);
  const locationConfig = useSelector((state: RootState) => state.map.locationConfig);
  const [permissionStatus, setPermissionStatus] = useState<PermissionState>('prompt');

  useEffect(() => {
    // Check geolocation permission status
    if ('permissions' in navigator) {
      navigator.permissions.query({ name: 'geolocation' })
        .then(status => {
          setPermissionStatus(status.state);
          status.onchange = () => setPermissionStatus(status.state);
        });
    }
  }, []);

  const updateConfig = (config: Partial<LocationConfig>) => {
    webSocketService.updateConfig(config);
  };

  return {
    isConnected,
    location,
    locationConfig,
    permissionStatus,
    updateConfig,
  };
}