import React from 'react';
import { MapPin } from 'lucide-react';
import type { LocationUpdate } from '../../types/api';

interface LocationTrackerProps {
  location?: LocationUpdate;
}

export function LocationTracker({ location }: LocationTrackerProps) {
  if (!location?.latitude || !location?.longitude) return null;

  return (
    <div className="flex items-center gap-2 rounded-md bg-white px-3 py-2 text-sm shadow-lg">
      <MapPin className="h-5 w-5" />
      <span>
        Location: {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
        {location.accuracy && ` (±${Math.round(location.accuracy)}m)`}
      </span>
    </div>
  );
}