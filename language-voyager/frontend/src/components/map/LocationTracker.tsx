import React from 'react';
import { useLocationTracking } from '@/hooks/useLocationTracking';
import { AlertTriangle, WifiOff, MapPin } from 'lucide-react';

export function LocationTracker() {
  const { isConnected, location, permissionStatus } = useLocationTracking();

  if (permissionStatus === 'denied') {
    return (
      <div className="fixed bottom-4 right-4 flex items-center gap-2 rounded-lg bg-destructive p-3 text-sm text-destructive-foreground">
        <AlertTriangle className="h-5 w-5" />
        <span>Location access denied. Please enable location services to use the map features.</span>
      </div>
    );
  }

  if (!isConnected) {
    return (
      <div className="fixed bottom-4 right-4 flex items-center gap-2 rounded-lg bg-muted p-3 text-sm text-muted-foreground">
        <WifiOff className="h-5 w-5" />
        <span>Reconnecting to location services...</span>
      </div>
    );
  }

  return location ? (
    <div className="fixed bottom-4 right-4 flex items-center gap-2 rounded-lg bg-primary p-3 text-sm text-primary-foreground">
      <MapPin className="h-5 w-5" />
      <span>
        Location: {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
        {location.accuracy && ` (±${Math.round(location.accuracy)}m)`}
      </span>
    </div>
  ) : null;
}