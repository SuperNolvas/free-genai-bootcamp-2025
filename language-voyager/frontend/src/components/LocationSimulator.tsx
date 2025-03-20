import React, { useState } from 'react';
import { MapPin, Navigation } from 'lucide-react';
import MapManager from '../services/arcgis';

const TOKYO_BOUNDS = {
  north: 35.8187,
  south: 35.5311,
  east: 139.9224,
  west: 139.5804
};

export function LocationSimulator() {
  const [showControls, setShowControls] = useState(false);
  const [currentLocation, setCurrentLocation] = useState({
    latitude: 35.6762, // Tokyo center
    longitude: 139.6503
  });

  const moveLocation = (direction: 'north' | 'south' | 'east' | 'west') => {
    const STEP = 0.001; // About 100m steps
    const newLocation = { ...currentLocation };

    switch (direction) {
      case 'north':
        newLocation.latitude = Math.min(newLocation.latitude + STEP, TOKYO_BOUNDS.north);
        break;
      case 'south':
        newLocation.latitude = Math.max(newLocation.latitude - STEP, TOKYO_BOUNDS.south);
        break;
      case 'east':
        newLocation.longitude = Math.min(newLocation.longitude + STEP, TOKYO_BOUNDS.east);
        break;
      case 'west':
        newLocation.longitude = Math.max(newLocation.longitude - STEP, TOKYO_BOUNDS.west);
        break;
    }

    setCurrentLocation(newLocation);
    MapManager.updateLocationMarker({
      latitude: newLocation.latitude,
      longitude: newLocation.longitude,
      accuracy: 10 // Simulated accuracy of 10 meters
    });
  };

  return (
    <div className="map-control absolute bottom-4 right-4">
      <button
        onClick={() => setShowControls(!showControls)}
        className="map-control flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-lg hover:bg-gray-100"
      >
        <MapPin className="h-4 w-4" />
      </button>
      {showControls && (
        <div className="map-control absolute bottom-12 right-0 w-64 rounded-lg bg-white p-4 shadow-lg">
          <div className="mb-4">
            <h3 className="font-medium">Location Simulator</h3>
            <p className="text-sm text-gray-600">
              Move around Tokyo using the controls
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div />
            <button
              onClick={() => moveLocation('north')}
              className="map-control rounded bg-blue-500 p-2 text-white hover:bg-blue-600"
            >
              ↑
            </button>
            <div />
            <button
              onClick={() => moveLocation('west')}
              className="map-control rounded bg-blue-500 p-2 text-white hover:bg-blue-600"
            >
              ←
            </button>
            <div className="rounded bg-gray-100 p-2 text-center text-sm">
              {currentLocation.latitude.toFixed(4)},{' '}
              {currentLocation.longitude.toFixed(4)}
            </div>
            <button
              onClick={() => moveLocation('east')}
              className="map-control rounded bg-blue-500 p-2 text-white hover:bg-blue-600"
            >
              →
            </button>
            <div />
            <button
              onClick={() => moveLocation('south')}
              className="map-control rounded bg-blue-500 p-2 text-white hover:bg-blue-600"
            >
              ↓
            </button>
            <div />
          </div>
        </div>
      )}
    </div>
  );
}