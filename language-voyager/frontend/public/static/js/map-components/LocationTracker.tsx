import React from 'react';
import { useLocationTracking } from '@/hooks/useLocationTracking';
import { MapPin } from 'lucide-react';

export function LocationTracker() {
  const { location } = useLocationTracking();

  return location ? (
    <div className="flex items-center gap-2 rounded-md bg-muted px-3 py-2 text-sm">
      <MapPin className="h-5 w-5" />
      <span>
        Location: {location.coords.latitude.toFixed(4)}, {location.coords.longitude.toFixed(4)}
        {location.coords.accuracy && ` (±${Math.round(location.coords.accuracy)}m)`}
      </span>
    </div>
  ) : null;
}